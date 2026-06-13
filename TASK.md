Ниже представлено подробное техническое задание для разработки фронтенд-части проекта **Steeper**, подготовленное на основе предоставленной документации бэкенда.

---

# Техническое Задание: Steeper Frontend

## 1. Стек технологий
* [cite_start]**Framework:** React (с использованием Vite.js для сборки). [cite: 1]
* [cite_start]**Язык:** TypeScript (строгая типизация всех API ответов и пропсов). [cite: 1]
* [cite_start]**Стилизация:** Tailwind CSS. [cite: 1]
* **State Management:** TanStack Query (React Query) — для серверного состояния, Zustand или Context API — для UI состояния.
* **WebSocket:** Родной `WebSocket` API или библиотека (например, `react-use-websocket`) с реализацией протокола аутентификации.

---

## 2. Дизайн и UX/UI
* [cite_start]**Стиль:** Строгое соответствие UI/UX Telegram (Desktop и Mobile версии). [cite: 1]
* [cite_start]**Эффекты:** Активное использование **Liquid Glass Effect** (стеклянный эффект с размытием фона) для сайдбаров, модальных окон и шапки чата. [cite: 1]
* [cite_start]**Адаптивность:** Полная поддержка мобильных устройств (интерфейс мобильного приложения Telegram) и десктопной версии (двухпанельный режим). [cite: 1]
* [cite_start]**Плавность:** Анимации переходов, плавный скролл в чате к новым сообщениям, отсутствие "прыжков" контента при загрузке. [cite: 1]

---

## 3. Интеграция с API (Endpoints)

На основе `Steeper-API-DOC.json`, фронтенд должен реализовать следующие методы:

### Пользователи и Аутентификация
* **POST `/v1/users/auth/login/password`**: Форма входа (Login/Password). [cite_start]Получение `access_token` и `refresh_token`. [cite: 11]
* [cite_start]**POST `/v1/users/auth/login/refresh`**: Автоматическое обновление токена при истечении access (использовать interceptors). [cite: 11]
* [cite_start]**GET `/v1/users/me`**: Загрузка данных профиля текущего пользователя (отображение в настройках/сайдбаре). [cite: 11]
* [cite_start]**GET `/v1/users/{user_id}`**: Просмотр информации о конкретном пользователе. [cite: 11]

### Управление Ботами
* [cite_start]**GET `/v1/bots/`**: Список всех подключенных ботов (с пагинацией). [cite: 11]
* [cite_start]**POST `/v1/bots/`**: Добавление нового бота через Token от BotFather. [cite: 11]
* [cite_start]**PATCH `/v1/bots/{bot_id}`**: Редактирование статуса бота (active/disabled/maintenance) или обновление токена. [cite: 11]
* [cite_start]**DELETE `/v1/bots/{bot_id}`**: Удаление бота из системы. [cite: 11]

### Чаты и Сообщения
* [cite_start]**GET `/v1/bots/{bot_id}/chats`**: Список чатов конкретного бота с превью последнего сообщения. [cite: 11]
* [cite_start]**GET `/v1/bots/{bot_id}/chats/{chat_id}/messages`**: История сообщений (Cursor-based пагинация: подгрузка при скролле вверх). [cite: 11]
* [cite_start]**POST `/v1/bots/{bot_id}/chats/{chat_id}/messages`**: Отправка текстового сообщения. [cite: 11]

### Рассылки (Broadcasts)
* [cite_start]**POST `/v1/broadcasts/`**: Создание рассылки (текст, фильтры по активности, планирование `schedule_at`). [cite: 11]
* [cite_start]**POST `/v1/broadcasts/{broadcast_id}/send`**: Запуск созданной рассылки. [cite: 11]
* [cite_start]**GET `/v1/broadcasts/{broadcast_id}/stats`**: Мониторинг статистики (всего/отправлено/ошибка) в реальном времени. [cite: 11]

### Аналитика и Система
* [cite_start]**GET `/v1/bots/{bot_id}/analytics/summary`**: Дашборд с показателями (Users, Chats, Messages, DAU). [cite: 11]
* [cite_start]**GET `/health/`**: Проверка доступности сервиса. [cite: 11]

---

## 4. Работа с WebSocket (Real-time)

Реализация должна строго следовать протоколу, описанному в `CLAUDE.md`, чтобы избежать утечек памяти и багов дублирования:

1.  **Установление соединения:** Подключение к эндпоинту.
2.  **Фаза аутентификации:** В течение **5 секунд** после открытия сокета фронтенд **обязан** отправить сообщение:
    ```json
    {"action": "authenticate", "token": "<access_jwt>"}
    ```
    [cite_start]Если токен не отправлен или невалиден, сервер закроет соединение (code 1008). [cite: 10]
3.  **Подписки:** Для получения сообщений в реальном времени нужно отправить:
    * [cite_start]`{"action": "subscribe", "chat_id": "..."}` — для конкретного чата. [cite: 10]
    * [cite_start]`{"action": "subscribe", "bot_id": "..."}` — для обновлений по всему боту (например, счетчик нечитанных). [cite: 10]
4.  [cite_start]**Heartbeat:** Периодическая отправка `{"action": "ping"}` для поддержания соединения (ожидание ответа `pong`). [cite: 10]
5.  **Обработка событий:** При получении `WSDownlinkEnvelope` от сервера, фронтенд должен мгновенно обновлять список сообщений или список чатов без перезагрузки страницы.

---

## 5. Docker и Запуск

Проект должен быть упакован в Docker. [cite_start]В корневой директории (backend/) необходимо обновить `Makefile` и `docker-compose.yml`. [cite: 1, 12]

### Структура папок
```text
.
├── backend/        # Текущий проект
└── frontend/       # Новый проект React + Vite
```

### Команды Makefile
Добавить в существующий `backend/Makefile`:
```makefile
# Run both Backend and Frontend in development mode
.PHONY: run-fullstack-dev
run-fullstack-dev:
	$(DOCKER_COMPOSE_DEV) up --build

# Run both Backend and Frontend in production mode
.PHONY: run-fullstack
run-fullstack:
	$(DOCKER_COMPOSE) up --build -d
```

### Требования к Frontend Docker:
* **Dev:** Использование `node:20-alpine`, проброс портов (обычно 5173), поддержка Hot Module Replacement (HMR).
* **Prod:** Многоэтапная сборка (multi-stage build) — сборка через Node.js и раздача статики через **Nginx**.

---

## 6. Критерии приемки
1.  [cite_start]**Отсутствие багов WS:** При переключении между чатами подписки должны корректно очищаться (`unsubscribe`), чтобы сообщения из одного чата не всплывали в другом. [cite: 10]
2.  [cite_start]**Валидация:** Все ошибки API (422, 401, 403) должны обрабатываться и выводиться пользователю в виде Toast-уведомлений. [cite: 11]
3.  **Performance:** Оптимизация рендеринга больших списков сообщений (virtual list при необходимости).
