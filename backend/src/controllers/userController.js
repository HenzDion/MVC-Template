import * as userModel from '../models/userModel.js';

const writableFields = {
  firstName: 'first_name',
  lastName: 'last_name',
  email: 'email',
  phone: 'phone',
  bio: 'bio',
  avatarUrl: 'avatar_url',
};

function badRequest(message) {
  const error = new Error(message);
  error.status = 400;
  return error;
}

function validateProfile(body, { partial = false } = {}) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    throw badRequest('Request body must be a JSON object.');
  }

  const unknownFields = Object.keys(body).filter(
    (field) => !Object.hasOwn(writableFields, field)
  );
  if (unknownFields.length > 0) {
    throw badRequest(`Unknown field: ${unknownFields.join(', ')}`);
  }

  if (!partial) {
    for (const field of ['firstName', 'lastName', 'email']) {
      if (typeof body[field] !== 'string' || body[field].trim() === '') {
        throw badRequest(`${field} is required and must be a non-empty string.`);
      }
    }
  }

  const fields = {};
  for (const [field, column] of Object.entries(writableFields)) {
    if (!Object.hasOwn(body, field)) continue;

    const value = body[field];
    if (value !== null && typeof value !== 'string') {
      throw badRequest(`${field} must be a string or null.`);
    }
    if (['firstName', 'lastName', 'email'].includes(field) &&
        (value === null || value.trim() === '')) {
      throw badRequest(`${field} must be a non-empty string.`);
    }
    fields[field] = value === null ? null : value.trim();
  }

  if (Object.hasOwn(fields, 'email') &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email)) {
    throw badRequest('email must be a valid email address.');
  }

  if (partial && Object.keys(fields).length === 0) {
    throw badRequest('Provide at least one profile field to update.');
  }

  return fields;
}

function parseId(value) {
  if (!/^\d+$/.test(value) || Number(value) < 1) {
    throw badRequest('id must be a positive integer.');
  }
  return Number(value);
}

export async function listUsers(_request, response, next) {
  try {
    const users = await userModel.getAllUsers();
    response.json({ data: users });
  } catch (error) {
    next(error);
  }
}

export async function getUser(request, response, next) {
  try {
    const user = await userModel.getUserById(parseId(request.params.id));
    if (!user) return response.status(404).json({ error: 'User not found.' });
    response.json({ data: user });
  } catch (error) {
    next(error);
  }
}

export async function createUser(request, response, next) {
  try {
    const fields = validateProfile(request.body);
    if (fields.email !== undefined) fields.email = fields.email.toLowerCase();
    const user = await userModel.createUser(fields);
    response.status(201).json({ data: user });
  } catch (error) {
    next(error);
  }
}

export async function updateUser(request, response, next) {
  try {
    const id = parseId(request.params.id);
    const fields = validateProfile(request.body, { partial: true });
    if (fields.email !== undefined) fields.email = fields.email.toLowerCase();
    const user = await userModel.updateUser(id, fields);
    if (!user) return response.status(404).json({ error: 'User not found.' });
    response.json({ data: user });
  } catch (error) {
    next(error);
  }
}

export async function deleteUser(request, response, next) {
  try {
    const deleted = await userModel.deleteUser(parseId(request.params.id));
    if (!deleted) return response.status(404).json({ error: 'User not found.' });
    response.status(204).end();
  } catch (error) {
    next(error);
  }
}