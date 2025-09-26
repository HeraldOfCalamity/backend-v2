from __future__ import annotations
from datetime import date, datetime, time
from typing import Any, Dict, List, Tuple

from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from bson.son import SON

from app.infrastructure.schemas.cita import Cita
from app.infrastructure.schemas.estadoCita import EstadoCita
from app.infrastructure.schemas.especialidad import Especialidad
from app.infrastructure.schemas.user import User  # <- para conocer el nombre de la colección 'users'

# ⬇️ Ajusta este import si tu módulo se llama distinto:
from app.infrastructure.schemas.especialista import Especialista  # <- ajustar si es necesario


# ----------------- Utilidades de tiempo y colección -----------------
def _bounds(from_date: date | None, to_date: date | None) -> Tuple[datetime, datetime]:
    today = date.today()
    start = from_date or date(today.year, 1, 1)
    end = to_date or date(today.year, 12, 31)
    return datetime.combine(start, time.min), datetime.combine(end, time.max)

async def _coll() -> AsyncIOMotorCollection:
    return Cita.get_motor_collection()

def _match(tenant_id: str, start: datetime, end: datetime) -> Dict[str, Any]:
    return {
        "$match": {
            "tenant_id": PydanticObjectId(tenant_id),
            "fecha_inicio": {"$gte": start, "$lte": end},
        }
    }

# ----------------- Pipelines base -----------------
def _group_total_por_mes() -> List[Dict[str, Any]]:
    return [
        {
            "$group": {
                "_id": {"month": {"$dateToString": {"format": "%Y-%m", "date": "$fecha_inicio"}}},
                "count": {"$sum": 1},
            }
        },
        {"$project": {"_id": 0, "month": "$_id.month", "count": 1}},
        {"$sort": SON([("month", 1)])},
    ]

def _group_generic_por_mes_key(field_expr: str) -> List[Dict[str, Any]]:
    return [
        {
            "$group": {
                "_id": {
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$fecha_inicio"}},
                    "key": field_expr,
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$group": {
                "_id": "$_id.month",
                "items": {"$push": {"key": "$_id.key", "count": "$count"}},
                "total": {"$sum": "$count"},
            }
        },
        {"$project": {"_id": 0, "month": "$_id", "items": 1, "total": 1}},
        {"$sort": SON([("month", 1)])},
    ]

def _group_por_mes_lookup_estado(estado_coll_name: str) -> List[Dict[str, Any]]:
    return [
        {
            "$lookup": {
                "from": estado_coll_name,
                "let": {"tid": "$tenant_id", "e_id": "$estado_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$tenant_id", "$$tid"]},
                                    {"$eq": ["$estado_id", "$$e_id"]},
                                ]
                            }
                        }
                    },
                    {"$project": {"_id": 0, "nombre": 1}},
                ],
                "as": "estado_doc",
            }
        },
        {"$set": {"estado_nombre": {"$ifNull": [{"$first": "$estado_doc.nombre"}, "desconocido"]}}},
        {"$unset": "estado_doc"},
        {
            "$group": {
                "_id": {
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$fecha_inicio"}},
                    "key": "$estado_nombre",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$group": {
                "_id": "$_id.month",
                "items": {"$push": {"key": "$_id.key", "count": "$count"}},
                "total": {"$sum": "$count"},
            }
        },
        {"$project": {"_id": 0, "month": "$_id", "items": 1, "total": 1}},
        {"$sort": SON([("month", 1)])},
    ]

def _group_por_mes_lookup_especialidad(esp_coll_name: str) -> List[Dict[str, Any]]:
    return [
        {
            "$lookup": {
                "from": esp_coll_name,
                "let": {"tid": "$tenant_id", "esp_id": "$especialidad_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$tenant_id", "$$tid"]},
                                    {"$eq": ["$_id", "$$esp_id"]},
                                ]
                            }
                        }
                    },
                    {"$project": {"_id": 0, "nombre": 1}},
                ],
                "as": "esp_doc",
            }
        },
        {"$set": {"esp_nombre": {"$ifNull": [{"$first": "$esp_doc.nombre"}, "sin especialidad"]}}},
        {"$unset": "esp_doc"},
        {
            "$group": {
                "_id": {
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$fecha_inicio"}},
                    "key": "$esp_nombre",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$group": {
                "_id": "$_id.month",
                "items": {"$push": {"key": "$_id.key", "count": "$count"}},
                "total": {"$sum": "$count"},
            }
        },
        {"$project": {"_id": 0, "month": "$_id", "items": 1, "total": 1}},
        {"$sort": SON([("month", 1)])},
    ]

# ----------------- Especialistas disponibles (para mostrar también con 0) -----------------
async def _all_especialistas_names(tenant_id: str) -> list[str]:
    """
    Devuelve la lista de todos los especialistas del tenant con su nombre visible,
    resolviendo (Especialista.user_id) -> User.name + ' ' + User.lastname.
    """
    esp_coll = Especialista.get_motor_collection()
    users_coll_name = User.get_motor_collection().name  # 'users'

    pipeline = [
        {"$match": {"tenant_id": PydanticObjectId(tenant_id)}},
        {
            "$lookup": {
                "from": users_coll_name,
                "let": {"tid": "$tenant_id", "uid": "$user_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$tenant_id", "$$tid"]},
                                    {"$eq": ["$_id", "$$uid"]},
                                    {"$eq": ["$isActive", True]},
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "fullName": {
                                "$trim": {
                                    "input": {
                                        "$concat": [
                                            {"$ifNull": ["$name", ""]}, " ",
                                            {"$ifNull": ["$lastname", ""]}
                                        ]
                                    }
                                }
                            }
                        }
                    },
                ],
                "as": "user_doc",
            }
        },
        {"$set": {"display": {"$ifNull": [{"$first": "$user_doc.fullName"}, None]}}},
        {"$match": {"display": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$display"}},                 # deduplicar
        {"$project": {"_id": 0, "name": "$_id"}},
        {"$sort": SON([("name", 1)])},
    ]

    cursor = esp_coll.aggregate(pipeline)
    return [doc["name"] async for doc in cursor]


# ----------------- Reporte principal -----------------
async def overview_report(tenant_id: str, from_date: date | None, to_date: date | None) -> Dict[str, Any]:
    start, end = _bounds(from_date, to_date)
    coll = await _coll()

    # ⚠️ No usar await aquí; Beanie retorna la colección sincrónicamente
    estado_coll_name = EstadoCita.get_motor_collection().name
    esp_coll_name = Especialidad.get_motor_collection().name

    async def _run(stages: List[Dict[str, Any]]):
        pipeline = [_match(tenant_id, start, end), *stages]
        cursor = coll.aggregate(pipeline)
        return [doc async for doc in cursor]

    totales = await _run(_group_total_por_mes())
    por_estado = await _run(_group_por_mes_lookup_estado(estado_coll_name))
    por_especialidad = await _run(_group_por_mes_lookup_especialidad(esp_coll_name))
    # especialista: usamos el nombre denormalizado guardado en Cita (ajusta el campo si es distinto)
    por_especialista = await _run(_group_generic_por_mes_key("$especialista_name"))

    todos = await _all_especialistas_names(tenant_id)

    return {
        "rango": {"from": start.date().isoformat(), "to": end.date().isoformat()},
        "totales_por_mes": totales,
        "por_estado": por_estado,
        "por_especialidad": por_especialidad,
        "por_especialista": por_especialista,
        "todos_los_especialistas": todos,   # <- para forzar claves en el front
    }
