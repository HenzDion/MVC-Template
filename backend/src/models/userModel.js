import pool from '../config/db.js';

const userColumns = `
  id,
  first_name AS "firstName",
  last_name AS "lastName",
  email,
  phone,
  bio,
  avatar_url AS "avatarUrl",
  created_at AS "createdAt",
  updated_at AS "updatedAt"
`;

export async function getAllUsers() {
  const result = await pool.query(
    `SELECT ${userColumns} FROM users ORDER BY id ASC`
  );
  return result.rows;
}

export async function getUserById(id) {
  const result = await pool.query(
    `SELECT ${userColumns} FROM users WHERE id = $1`,
    [id]
  );
  return result.rows[0] ?? null;
}

export async function createUser(user) {
  const { firstName, lastName, email, phone, bio, avatarUrl } = user;
  const result = await pool.query(
    `INSERT INTO users (first_name, last_name, email, phone, bio, avatar_url)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING ${userColumns}`,
    [firstName, lastName, email, phone, bio, avatarUrl]
  );
  return result.rows[0];
}

export async function updateUser(id, fields) {
  const columnByField = {
    firstName: 'first_name',
    lastName: 'last_name',
    email: 'email',
    phone: 'phone',
    bio: 'bio',
    avatarUrl: 'avatar_url',
  };
  const entries = Object.entries(fields);
  const assignments = entries.map(
    ([field], index) => `${columnByField[field]} = $${index + 1}`
  );
  const values = entries.map(([, value]) => value);
  values.push(id);

  const result = await pool.query(
    `UPDATE users
     SET ${assignments.join(', ')}, updated_at = CURRENT_TIMESTAMP
     WHERE id = $${values.length}
     RETURNING ${userColumns}`,
    values
  );
  return result.rows[0] ?? null;
}

export async function deleteUser(id) {
  const result = await pool.query(
    'DELETE FROM users WHERE id = $1 RETURNING id',
    [id]
  );
  return result.rowCount > 0;
}