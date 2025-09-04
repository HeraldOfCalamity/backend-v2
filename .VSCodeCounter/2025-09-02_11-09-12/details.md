# Details

Date : 2025-09-02 11:09:12

Directory c:\\Users\\relee\\Code\\Benedetta\\trabajo-grado-v2\\backend-v2\\app

Total : 61 files,  1973 codes, 44 comments, 560 blanks, all 2577 lines

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [app/application/services/auth\_service.py](/app/application/services/auth_service.py) | Python | 24 | 0 | 9 | 33 |
| [app/application/services/notification\_service.py](/app/application/services/notification_service.py) | Python | 16 | 0 | 5 | 21 |
| [app/core/auth\_utils.py](/app/core/auth_utils.py) | Python | 9 | 0 | 4 | 13 |
| [app/core/config.py](/app/core/config.py) | Python | 14 | 0 | 5 | 19 |
| [app/core/db.py](/app/core/db.py) | Python | 33 | 0 | 3 | 36 |
| [app/core/exceptions.py](/app/core/exceptions.py) | Python | 36 | 0 | 7 | 43 |
| [app/core/security.py](/app/core/security.py) | Python | 55 | 0 | 16 | 71 |
| [app/domain/entities/cita\_entity.py](/app/domain/entities/cita_entity.py) | Python | 25 | 0 | 5 | 30 |
| [app/domain/entities/especialidad\_entity.py](/app/domain/entities/especialidad_entity.py) | Python | 20 | 0 | 3 | 23 |
| [app/domain/entities/especialista\_entity.py](/app/domain/entities/especialista_entity.py) | Python | 37 | 0 | 8 | 45 |
| [app/domain/entities/estadoCita\_entity.py](/app/domain/entities/estadoCita_entity.py) | Python | 6 | 0 | 2 | 8 |
| [app/domain/entities/officeConfig\_entity.py](/app/domain/entities/officeConfig_entity.py) | Python | 7 | 0 | 3 | 10 |
| [app/domain/entities/office\_entity.py](/app/domain/entities/office_entity.py) | Python | 7 | 0 | 2 | 9 |
| [app/domain/entities/paciente\_entity.py](/app/domain/entities/paciente_entity.py) | Python | 33 | 0 | 10 | 43 |
| [app/domain/entities/permission\_entity.py](/app/domain/entities/permission_entity.py) | Python | 10 | 0 | 3 | 13 |
| [app/domain/entities/role\_entity.py](/app/domain/entities/role_entity.py) | Python | 18 | 0 | 5 | 23 |
| [app/domain/entities/tratamiento\_entity.py](/app/domain/entities/tratamiento_entity.py) | Python | 17 | 0 | 3 | 20 |
| [app/domain/entities/user\_entity.py](/app/domain/entities/user_entity.py) | Python | 35 | 5 | 5 | 45 |
| [app/infrastructure/notifiers/email\_notifier.py](/app/infrastructure/notifiers/email_notifier.py) | Python | 18 | 0 | 7 | 25 |
| [app/infrastructure/notifiers/push\_notifier.py](/app/infrastructure/notifiers/push_notifier.py) | Python | 2 | 0 | 0 | 2 |
| [app/infrastructure/repositories/cita\_repo.py](/app/infrastructure/repositories/cita_repo.py) | Python | 192 | 3 | 65 | 260 |
| [app/infrastructure/repositories/especialidad\_repo.py](/app/infrastructure/repositories/especialidad_repo.py) | Python | 59 | 0 | 14 | 73 |
| [app/infrastructure/repositories/especialista\_repo.py](/app/infrastructure/repositories/especialista_repo.py) | Python | 116 | 0 | 31 | 147 |
| [app/infrastructure/repositories/estadoCita\_repo.py](/app/infrastructure/repositories/estadoCita_repo.py) | Python | 19 | 0 | 5 | 24 |
| [app/infrastructure/repositories/officeConfig\_repo.py](/app/infrastructure/repositories/officeConfig_repo.py) | Python | 24 | 0 | 8 | 32 |
| [app/infrastructure/repositories/office\_repo.py](/app/infrastructure/repositories/office_repo.py) | Python | 3 | 0 | 2 | 5 |
| [app/infrastructure/repositories/paciente\_repo.py](/app/infrastructure/repositories/paciente_repo.py) | Python | 79 | 11 | 31 | 121 |
| [app/infrastructure/repositories/permission\_repo.py](/app/infrastructure/repositories/permission_repo.py) | Python | 20 | 0 | 6 | 26 |
| [app/infrastructure/repositories/role\_repo.py](/app/infrastructure/repositories/role_repo.py) | Python | 50 | 5 | 15 | 70 |
| [app/infrastructure/repositories/tratamiento\_repo.py](/app/infrastructure/repositories/tratamiento_repo.py) | Python | 45 | 0 | 15 | 60 |
| [app/infrastructure/repositories/user\_repo.py](/app/infrastructure/repositories/user_repo.py) | Python | 109 | 8 | 32 | 149 |
| [app/infrastructure/schemas/cita.py](/app/infrastructure/schemas/cita.py) | Python | 45 | 0 | 7 | 52 |
| [app/infrastructure/schemas/especialidad.py](/app/infrastructure/schemas/especialidad.py) | Python | 14 | 0 | 5 | 19 |
| [app/infrastructure/schemas/especialista.py](/app/infrastructure/schemas/especialista.py) | Python | 21 | 0 | 4 | 25 |
| [app/infrastructure/schemas/estadoCita.py](/app/infrastructure/schemas/estadoCita.py) | Python | 16 | 0 | 3 | 19 |
| [app/infrastructure/schemas/office.py](/app/infrastructure/schemas/office.py) | Python | 10 | 0 | 5 | 15 |
| [app/infrastructure/schemas/officeConfig.py](/app/infrastructure/schemas/officeConfig.py) | Python | 10 | 0 | 4 | 14 |
| [app/infrastructure/schemas/paciente.py](/app/infrastructure/schemas/paciente.py) | Python | 14 | 0 | 5 | 19 |
| [app/infrastructure/schemas/permission.py](/app/infrastructure/schemas/permission.py) | Python | 12 | 0 | 4 | 16 |
| [app/infrastructure/schemas/role.py](/app/infrastructure/schemas/role.py) | Python | 13 | 0 | 4 | 17 |
| [app/infrastructure/schemas/tratamiento.py](/app/infrastructure/schemas/tratamiento.py) | Python | 13 | 0 | 5 | 18 |
| [app/infrastructure/schemas/user.py](/app/infrastructure/schemas/user.py) | Python | 21 | 0 | 5 | 26 |
| [app/main.py](/app/main.py) | Python | 34 | 0 | 8 | 42 |
| [app/presentation/api/v1/auth\_routes.py](/app/presentation/api/v1/auth_routes.py) | Python | 9 | 0 | 4 | 13 |
| [app/presentation/api/v1/cita\_routes.py](/app/presentation/api/v1/cita_routes.py) | Python | 62 | 1 | 18 | 81 |
| [app/presentation/api/v1/especialidad\_routes.py](/app/presentation/api/v1/especialidad_routes.py) | Python | 27 | 0 | 7 | 34 |
| [app/presentation/api/v1/especialista\_routes.py](/app/presentation/api/v1/especialista_routes.py) | Python | 81 | 0 | 17 | 98 |
| [app/presentation/api/v1/officeConfig\_routes.py](/app/presentation/api/v1/officeConfig_routes.py) | Python | 16 | 0 | 6 | 22 |
| [app/presentation/api/v1/paciente\_routes.py](/app/presentation/api/v1/paciente_routes.py) | Python | 79 | 8 | 15 | 102 |
| [app/presentation/api/v1/permission\_routes.py](/app/presentation/api/v1/permission_routes.py) | Python | 11 | 0 | 5 | 16 |
| [app/presentation/api/v1/role\_routes.py](/app/presentation/api/v1/role_routes.py) | Python | 26 | 0 | 7 | 33 |
| [app/presentation/api/v1/tratamiento\_routes.py](/app/presentation/api/v1/tratamiento_routes.py) | Python | 27 | 0 | 7 | 34 |
| [app/presentation/api/v1/user\_routes.py](/app/presentation/api/v1/user_routes.py) | Python | 27 | 0 | 10 | 37 |
| [app/scripts/init\_admin\_role.py](/app/scripts/init_admin_role.py) | Python | 31 | 0 | 10 | 41 |
| [app/scripts/init\_admin\_user.py](/app/scripts/init_admin_user.py) | Python | 47 | 0 | 11 | 58 |
| [app/scripts/init\_estados\_cita.py](/app/scripts/init_estados_cita.py) | Python | 31 | 0 | 7 | 38 |
| [app/scripts/init\_office\_config.py](/app/scripts/init_office_config.py) | Python | 30 | 0 | 11 | 41 |
| [app/scripts/init\_permissions.py](/app/scripts/init_permissions.py) | Python | 56 | 3 | 19 | 78 |
| [app/shared/dto/mailData\_dto.py](/app/shared/dto/mailData_dto.py) | Python | 11 | 0 | 3 | 14 |
| [app/shared/dto/token\_dto.py](/app/shared/dto/token_dto.py) | Python | 8 | 0 | 3 | 11 |
| [app/shared/utils.py](/app/shared/utils.py) | Python | 33 | 0 | 12 | 45 |

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)