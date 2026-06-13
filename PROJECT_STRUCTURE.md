.
├── backend
│   ├── alembic.ini
│   ├── celerybeat-schedule
│   ├── celerybeat-schedule-shm
│   ├── celerybeat-schedule-wal
│   ├── celery_tasks
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── types.py
│   ├── CLAUDE.md
│   ├── docs
│   │   └── readme
│   │       ├── architecture.md
│   │       ├── contributing.md
│   │       └── infra.md
│   ├── infra
│   │   ├── docker
│   │   │   ├── Dockerfile
│   │   │   └── Dockerfile.dev
│   │   ├── docker-compose.override.yml
│   │   ├── docker-compose.yml
│   │   ├── nginx
│   │   │   ├── app.conf
│   │   │   ├── dev-nginx.conf
│   │   │   └── main.conf
│   │   ├── postgres
│   │   │   ├── Dockerfile-postgis
│   │   │   ├── init-postgis.sh
│   │   │   ├── postgresql.conf
│   │   │   └── setup-config.sh
│   │   ├── redis.conf
│   │   ├── requirements
│   │   │   ├── base.txt
│   │   │   ├── dev.txt
│   │   │   └── prod.txt
│   │   └── requirements.txt
│   ├── loggers
│   │   └── __init__.py
│   ├── logs
│   ├── Makefile
│   ├── migrations
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── versions
│   │       ├── 3c7a9b2e1f4d_add_login_password_to_users.py
│   │       ├── 515e6154818b_remove_phone_number.py
│   │       ├── 9a0e3f8c57e6_initial.py
│   │       ├── aee42dd2199f_remove_redundant_permission_field.py
│   │       ├── b8e4a1c2d3f5_remove_workspace_and_bot_roles.py
│   │       ├── c096e09e32e6_extended_soft_delete.py
│   │       ├── c9f5d2e1a4b6_drop_bots_owner_id.py
│   │       ├── d69ff11b09aa_use_telegram_auth.py
│   │       ├── da02a31de83d_use_timezone_aware.py
│   │       ├── e2a3b4c5d6f7_remove_users_telegram_id.py
│   │       ├── f1d8f11de7e7_add_is_default_workspace.py
│   │       ├── f3b4c5d6e7f8_drop_audit_logs_table.py
│   │       └── __init__.py
│   ├── models
│   │   └── __init__.py
│   ├── mypy.ini
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── README.md
│   ├── scripts
│   │   ├── check_env.py
│   │   ├── createsuperuser.py
│   │   └── __init__.py
│   ├── src
│   │   ├── analytics
│   │   │   ├── dependencies.py
│   │   │   ├── __init__.py
│   │   │   ├── routers
│   │   │   │   ├── analytics.py
│   │   │   │   └── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── usecases
│   │   │       ├── get_bot_summary.py
│   │   │       ├── get_dashboard_stats.py
│   │   │       ├── __init__.py
│   │   │       └── log_admin_action.py
│   │   ├── bot
│   │   │   ├── dependencies.py
│   │   │   ├── enums.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── repositories
│   │   │   │   └── bot.py
│   │   │   ├── routers.py
│   │   │   ├── schemas.py
│   │   │   ├── services
│   │   │   │   └── bot.py
│   │   │   └── usecases
│   │   │       ├── create_bot.py
│   │   │       ├── delete_bot.py
│   │   │       ├── __init__.py
│   │   │       └── update_bot.py
│   │   ├── communication
│   │   │   ├── chat
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routers.py
│   │   │   │   └── usecases
│   │   │   │       ├── __init__.py
│   │   │   │       ├── list_chats.py
│   │   │   │       ├── list_messages.py
│   │   │   │       └── send_message.py
│   │   │   ├── dependencies.py
│   │   │   ├── enums.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── repositories
│   │   │   │   ├── chat.py
│   │   │   │   └── message.py
│   │   │   ├── routers.py
│   │   │   ├── schemas.py
│   │   │   └── usecases
│   │   │       ├── handle_webhook.py
│   │   │       ├── __init__.py
│   │   │       └── log_bot_message.py
│   │   ├── core
│   │   │   ├── database
│   │   │   │   ├── base.py
│   │   │   │   ├── engine.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mixins.py
│   │   │   │   ├── repositories.py
│   │   │   │   ├── session.py
│   │   │   │   ├── transactions.py
│   │   │   │   ├── types.py
│   │   │   │   └── uow
│   │   │   │       ├── abstract.py
│   │   │   │       ├── application.py
│   │   │   │       ├── __init__.py
│   │   │   │       └── sqlalchemy.py
│   │   │   ├── email_service
│   │   │   │   ├── config.py
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── factory.py
│   │   │   │   ├── fastapi_mailer.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── interfaces.py
│   │   │   │   ├── mailjet_mailer.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── tasks.py
│   │   │   │   └── templates
│   │   │   │       ├── base.html
│   │   │   │       ├── components
│   │   │   │       │   ├── _button.html
│   │   │   │       │   ├── _message.html
│   │   │   │       │   └── _title.html
│   │   │   │       ├── notification.html
│   │   │   │       ├── reset_password.html
│   │   │   │       ├── user_request_notification.html
│   │   │   │       ├── verification.html
│   │   │   │       └── workspace_invite.html
│   │   │   ├── errors
│   │   │   │   ├── enums.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── handlers.py
│   │   │   │   └── __init__.py
│   │   │   ├── i18n
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── enums.py
│   │   │   │   ├── errors
│   │   │   │   │   ├── en.py
│   │   │   │   │   ├── ru.py
│   │   │   │   │   └── uz.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── utils.py
│   │   │   ├── __init__.py
│   │   │   ├── limiter
│   │   │   │   ├── depends.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── script.py
│   │   │   ├── middleware.py
│   │   │   ├── pagination
│   │   │   │   ├── __init__.py
│   │   │   │   └── schemas.py
│   │   │   ├── patterns
│   │   │   │   ├── __init__.py
│   │   │   │   └── singleton.py
│   │   │   ├── redis
│   │   │   │   ├── core.py
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── lifecycle.py
│   │   │   ├── schemas.py
│   │   │   ├── services.py
│   │   │   ├── storage
│   │   │   │   ├── __init__.py
│   │   │   │   └── s3
│   │   │   │       ├── adapter.py
│   │   │   │       ├── dependencies.py
│   │   │   │       ├── __init__.py
│   │   │   │       └── interface.py
│   │   │   ├── utils
│   │   │   │   ├── coroutine_runner.py
│   │   │   │   ├── datetime_utils.py
│   │   │   │   ├── encryption.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── retry.py
│   │   │   │   └── security.py
│   │   │   └── validations.py
│   │   ├── crm
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── repositories.py
│   │   │   ├── routers.py
│   │   │   ├── schemas.py
│   │   │   └── usecases
│   │   │       ├── get_audience_list.py
│   │   │       ├── __init__.py
│   │   │       ├── sync_user.py
│   │   │       └── update_user_tags.py
│   │   ├── __init__.py
│   │   ├── integrations
│   │   │   └── telegram
│   │   │       ├── bot
│   │   │       │   └── telegram_bot_api.py
│   │   │       └── dependencies.py
│   │   ├── main
│   │   │   ├── config.py
│   │   │   ├── __init__.py
│   │   │   ├── lifespan.py
│   │   │   ├── presentation.py
│   │   │   ├── route_logging.py
│   │   │   ├── sentry.py
│   │   │   └── web.py
│   │   ├── marketing
│   │   │   ├── dependencies.py
│   │   │   ├── enums.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── repositories
│   │   │   │   ├── broadcast_delivery.py
│   │   │   │   └── broadcast.py
│   │   │   ├── routers.py
│   │   │   ├── schemas.py
│   │   │   ├── tasks.py
│   │   │   └── usecases
│   │   │       ├── create_campaign.py
│   │   │       ├── get_campaign_stats.py
│   │   │       ├── __init__.py
│   │   │       ├── launch_broadcast.py
│   │   │       └── process_broadcast.py
│   │   ├── realtime
│   │   │   ├── broker.py
│   │   │   ├── consumers.py
│   │   │   ├── dependencies.py
│   │   │   ├── enums.py
│   │   │   ├── __init__.py
│   │   │   ├── manager.py
│   │   │   ├── routers.py
│   │   │   ├── schemas.py
│   │   │   └── usecases
│   │   │       ├── __init__.py
│   │   │       └── websocket_endpoint.py
│   │   ├── system
│   │   │   ├── dependencies.py
│   │   │   ├── __init__.py
│   │   │   ├── routers.py
│   │   │   ├── schemas.py
│   │   │   └── services.py
│   │   └── user
│   │       ├── auth
│   │       │   ├── dependencies.py
│   │       │   ├── __init__.py
│   │       │   ├── jwt_payload_schema.py
│   │       │   ├── permissions
│   │       │   │   ├── checker.py
│   │       │   │   ├── enum.py
│   │       │   │   ├── __init__.py
│   │       │   │   └── role_matrix.py
│   │       │   ├── redis_scripts.py
│   │       │   ├── REFRESH_TOKEN_IMPLEMENTATION.md
│   │       │   ├── routers.py
│   │       │   ├── schemas.py
│   │       │   ├── security.py
│   │       │   ├── services
│   │       │   │   └── __init__.py
│   │       │   ├── token_helpers.py
│   │       │   └── usecases
│   │       │       ├── get_access_by_refresh.py
│   │       │       ├── __init__.py
│   │       │       └── password_auth.py
│   │       ├── dependencies.py
│   │       ├── enums.py
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── repositories.py
│   │       ├── routers.py
│   │       ├── schemas.py
│   │       ├── services.py
│   │       └── usecases
│   │           └── __init__.py
│   └── tests
│       ├── auth
│       │   ├── __init__.py
│       │   ├── test_refresh_rotation.py
│       │   └── test_token_helpers_security.py
│       ├── core
│       │   ├── test_coroutine_runner.py
│       │   ├── test_datetime_utils.py
│       │   ├── test_email_tasks_and_mailer.py
│       │   ├── test_error_handlers.py
│       │   ├── test_middleware_postgres.py
│       │   ├── test_middlewares_http.py
│       │   ├── test_redis_lifecycle.py
│       │   └── test_security_utils.py
│       ├── email
│       │   ├── __init__.py
│       │   ├── mocks.py
│       │   └── test_email_service.py
│       ├── __init__.py
│       ├── main
│       │   ├── test_config.py
│       │   └── test_route_logging.py
│       ├── storage
│       │   └── test_s3_adapter.py
│       └── system
│           └── test_system_routers.py
└── frontend

71 directories, 253 files
