# User Profile API

Express REST API for creating, reading, updating, and deleting user profiles with PostgreSQL.

## Setup

1. Install Node.js 18 or later and PostgreSQL.
2. Create a PostgreSQL database named `user_profiles` (or choose another name).
3. Copy `.env.example` to `.env` and set `DATABASE_URL` to your PostgreSQL connection string.
4. From this directory, install packages and create the table:

```sh
npm install
psql "$DATABASE_URL" -f src/db/schema.sql
```

5. Start the API with `npm run dev` or `npm start`. It listens on port 3000 by default.

## Endpoints

All endpoints are prefixed with `/api/users`. Profile fields are `firstName`, `lastName`, `email`, `phone`, `bio`, and `avatarUrl`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/users` | List profiles |
| GET | `/api/users/:id` | Get a profile |
| POST | `/api/users` | Create a profile; `firstName`, `lastName`, and `email` are required |
| PATCH | `/api/users/:id` | Update one or more profile fields |
| DELETE | `/api/users/:id` | Delete a profile |

Successful reads and writes return `{ "data": ... }`. Deletion returns `204 No Content`. Missing profiles return `404`; duplicate emails return `409`.

Example create request:

```json
{
  "firstName": "Ada",
  "lastName": "Lovelace",
  "email": "ada@example.com",
  "phone": "+1-555-0100",
  "bio": "Mathematician and writer"
}
```