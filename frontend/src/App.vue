<script setup>
import { computed, onMounted, ref } from 'vue';
import {
  ArrowDownUp,
  ArrowUpRight,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  CircleHelp,
  LoaderCircle,
  Mail,
  MapPin,
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  UserRound,
  UsersRound,
  X,
} from '@lucide/vue';

const API_URL = import.meta.env.VITE_API_URL || '/api/users';
const users = ref([]);
const selectedId = ref(null);
const query = ref('');
const loading = ref(true);
const apiOnline = ref(null);
const saving = ref(false);
const pageError = ref('');
const notice = ref('');
const modalOpen = ref(false);
const editingId = ref(null);
const searchInput = ref(null);
const formError = ref('');
const form = ref(emptyForm());

function emptyForm() {
  return { firstName: '', lastName: '', email: '', phone: '', bio: '', avatarUrl: '' };
}

const selectedUser = computed(() => users.value.find((user) => user.id === selectedId.value) ?? null);
const filteredUsers = computed(() => {
  const needle = query.value.trim().toLowerCase();
  if (!needle) return users.value;
  return users.value.filter((user) =>
    [user.firstName, user.lastName, user.email, user.phone]
      .filter(Boolean)
      .some((value) => value.toLowerCase().includes(needle)),
  );
});
function userInitials(user) {
  return `${user.firstName?.[0] ?? ''}${user.lastName?.[0] ?? ''}`.toUpperCase() || 'U';
}

function fullName(user) {
  return `${user.firstName} ${user.lastName}`.trim();
}

function formatDate(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value));
}

function setNotice(message) {
  notice.value = message;
  window.setTimeout(() => {
    if (notice.value === message) notice.value = '';
  }, 3200);
}

async function request(path = '', options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    });
  } catch {
    apiOnline.value = false;
    throw new Error('Could not reach the API. Check that the backend is running on port 3000.');
  }

  if (response.status === 204) return null;
  apiOnline.value = true;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status >= 500 && payload.error === 'Internal server error.') {
      throw new Error('The API is running, but could not read profiles. Check the PostgreSQL connection and backend logs.');
    }
    if (response.status >= 500 && !payload.error) {
      apiOnline.value = false;
      throw new Error('Could not reach the API. Check that the backend is running on port 3000.');
    }
    throw new Error(payload.error || 'Something went wrong. Please try again.');
  }
  return payload.data;
}

async function loadUsers() {
  loading.value = true;
  pageError.value = '';
  try {
    users.value = await request();
    if (!users.value.some((user) => user.id === selectedId.value)) {
      selectedId.value = users.value[0]?.id ?? null;
    }
  } catch (error) {
    pageError.value = error.message;
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  form.value = emptyForm();
  formError.value = '';
  modalOpen.value = true;
}

function openEdit(user) {
  editingId.value = user.id;
  form.value = {
    firstName: user.firstName ?? '',
    lastName: user.lastName ?? '',
    email: user.email ?? '',
    phone: user.phone ?? '',
    bio: user.bio ?? '',
    avatarUrl: user.avatarUrl ?? '',
  };
  formError.value = '';
  modalOpen.value = true;
}

function closeModal() {
  if (saving.value) return;
  modalOpen.value = false;
}

async function saveUser() {
  saving.value = true;
  formError.value = '';
  const payload = Object.fromEntries(
    Object.entries(form.value).map(([key, value]) => [key, value.trim()]),
  );
  try {
    const user = await request(editingId.value ? `/${editingId.value}` : '', {
      method: editingId.value ? 'PATCH' : 'POST',
      body: JSON.stringify(payload),
    });
    if (editingId.value) {
      users.value = users.value.map((item) => item.id === user.id ? user : item);
      setNotice('Profile changes saved');
    } else {
      users.value = [...users.value, user];
      selectedId.value = user.id;
      setNotice('Profile created');
    }
    modalOpen.value = false;
  } catch (error) {
    formError.value = error.message;
  } finally {
    saving.value = false;
  }
}

async function removeUser(user) {
  if (!window.confirm(`Delete ${fullName(user)}'s profile? This cannot be undone.`)) return;
  try {
    await request(`/${user.id}`, { method: 'DELETE' });
    users.value = users.value.filter((item) => item.id !== user.id);
    selectedId.value = users.value[0]?.id ?? null;
    setNotice('Profile deleted');
  } catch (error) {
    pageError.value = error.message;
  }
}

function focusSearch() {
  searchInput.value?.focus();
}

onMounted(loadUsers);
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand" href="#" aria-label="People home">
        <span class="brand-mark"><UsersRound :size="19" :stroke-width="2.2" /></span>
        <span class="brand-name">fieldnote<span>.</span></span>
      </a>

      <div class="workspace-switcher">
        <span class="workspace-monogram">N</span>
        <span class="workspace-copy"><strong>Northstar Studio</strong><small>Workspace</small></span>
        <ChevronDown :size="15" class="muted-icon" />
      </div>

      <p class="nav-caption">WORKSPACE</p>
      <nav class="primary-nav" aria-label="Main navigation">
        <a class="nav-item" href="#overview"><BriefcaseBusiness :size="17" /><span>Overview</span></a>
        <a class="nav-item active" href="#people" aria-current="page"><UsersRound :size="17" /><span>People</span><span class="nav-count">{{ users.length }}</span></a>
      </nav>

      <div class="sidebar-bottom">
        <div class="sidebar-note"><Sparkles :size="15" /><span>Small details.<br />Strong connections.</span></div>
        <button class="account-button" type="button">
          <span class="account-avatar">AM</span>
          <span class="account-copy"><strong>Alex Morgan</strong><small>Administrator</small></span>
          <MoreHorizontal :size="18" />
        </button>
      </div>
    </aside>

    <main id="people" class="main-content">
      <header class="topbar">
        <div class="breadcrumb"><span>Workspace</span><span class="crumb-slash">/</span><strong>People</strong></div>
        <div class="topbar-right"><span class="online-indicator" :class="{ offline: apiOnline === false }"><i></i> {{ apiOnline === null ? 'Checking API' : apiOnline ? 'API connected' : 'API offline' }}</span><button class="help-button" type="button" aria-label="Help" title="Help"><CircleHelp :size="18" /></button></div>
      </header>

      <section class="page-content">
        <div class="page-heading">
          <div>
            <div class="eyebrow"><span class="eyebrow-line"></span> PEOPLE DIRECTORY</div>
            <h1>Your people,<br class="mobile-break" /> <em>in one place.</em></h1>
            <p class="page-subtitle">A thoughtful home for the people you work with.</p>
          </div>
          <button class="primary-button" type="button" @click="openCreate"><Plus :size="17" /> Add person</button>
        </div>

        <div class="stat-strip">
          <div class="stat-item"><span class="stat-icon green"><UsersRound :size="17" /></span><span class="stat-label">TOTAL PEOPLE</span><strong>{{ users.length.toString().padStart(2, '0') }}</strong></div>
          <div class="stat-divider"></div>
          <div class="stat-item"><span class="stat-icon coral"><Sparkles :size="16" /></span><span class="stat-label">DIRECTORY STATUS</span><strong class="status-copy" :class="{ offline: apiOnline === false }"><i></i> {{ apiOnline === null ? 'Connecting' : apiOnline ? 'API available' : 'API unavailable' }}</strong></div>
          <div class="stat-spacer"></div>
          <button class="quiet-button" type="button" @click="loadUsers"><ArrowDownUp :size="15" /> Refresh</button>
        </div>

        <div class="directory-toolbar">
          <div class="section-title"><h2>All profiles</h2><span class="result-count">{{ filteredUsers.length }}</span></div>
          <div class="toolbar-actions">
            <label class="search-box"><Search :size="16" /><input ref="searchInput" v-model="query" type="search" placeholder="Search people..." aria-label="Search profiles" /><kbd @click="focusSearch">/</kbd></label>
            <button class="filter-button" type="button" disabled title="Filters coming soon"><SlidersHorizontal :size="16" /><span>Filter</span><span class="filter-dot"></span></button>
          </div>
        </div>

        <div v-if="pageError" class="alert-banner" role="alert"><span>{{ pageError }}</span><button type="button" aria-label="Dismiss error" @click="pageError = ''"><X :size="16" /></button></div>

        <div class="directory-layout">
          <section class="people-panel" aria-label="User profiles">
            <div class="table-head"><span>PERSON</span><span>CONTACT</span><span>ADDED</span><span></span></div>
            <div v-if="loading" class="loading-state"><LoaderCircle class="spin" :size="21" /><span>Gathering your people...</span></div>
            <div v-else-if="filteredUsers.length" class="people-list">
              <button v-for="(user, index) in filteredUsers" :key="user.id" class="person-row" :class="{ selected: selectedId === user.id }" type="button" :style="{ '--row-index': index }" @click="selectedId = user.id">
                <span class="person-cell"><span class="avatar" :class="`avatar-tone-${(index % 5) + 1}`"><img v-if="user.avatarUrl" :src="user.avatarUrl" :alt="''" /><span v-else>{{ userInitials(user) }}</span></span><span class="person-copy"><strong>{{ fullName(user) }}</strong><small>{{ user.bio || 'Profile member' }}</small></span></span>
                <span class="contact-cell"><span>{{ user.email }}</span><small>{{ user.phone || 'No phone added' }}</small></span>
                <span class="date-cell">{{ formatDate(user.createdAt) }}</span>
                <span class="row-arrow"><ArrowUpRight :size="16" /></span>
              </button>
            </div>
            <div v-else-if="query" class="empty-state"><span class="empty-icon"><Search :size="20" /></span><strong>No matches found</strong><p>Try another name, email, or phone number.</p><button type="button" @click="query = ''">Clear search</button></div>
            <div v-else class="empty-state"><span class="empty-icon"><UserRound :size="20" /></span><strong>A good place to start.</strong><p>Your directory is ready for its first profile.</p><button type="button" @click="openCreate"><Plus :size="15" /> Add the first person</button></div>
            <footer class="list-footer"><span>Showing {{ filteredUsers.length }} of {{ users.length }} profiles</span><span class="footer-sync"><Check :size="13" /> Live directory</span></footer>
          </section>

          <aside class="detail-panel" aria-label="Selected profile details">
            <template v-if="selectedUser">
              <div class="detail-topline"><span>PROFILE CARD</span><button class="icon-button" type="button" aria-label="Edit profile" title="Edit profile" @click="openEdit(selectedUser)"><Pencil :size="15" /></button></div>
              <div class="profile-hero">
                <div class="profile-avatar"><img v-if="selectedUser.avatarUrl" :src="selectedUser.avatarUrl" :alt="fullName(selectedUser)" /><span v-else>{{ userInitials(selectedUser) }}</span><i></i></div>
                <h3>{{ fullName(selectedUser) }}</h3><span class="member-badge"><i></i> Directory member</span>
              </div>
              <div class="detail-rule"></div>
              <div class="detail-fields">
                <div class="detail-field"><span class="detail-icon"><Mail :size="15" /></span><span><small>EMAIL ADDRESS</small><a :href="`mailto:${selectedUser.email}`">{{ selectedUser.email }}</a></span></div>
                <div class="detail-field"><span class="detail-icon"><UserRound :size="15" /></span><span><small>PHONE</small><a v-if="selectedUser.phone" :href="`tel:${selectedUser.phone}`">{{ selectedUser.phone }}</a><span v-else class="field-empty">Not provided</span></span></div>
                <div class="detail-field"><span class="detail-icon"><MapPin :size="15" /></span><span><small>ABOUT</small><span class="about-copy">{{ selectedUser.bio || 'No introduction added yet.' }}</span></span></div>
              </div>
              <div class="detail-bottom"><span>ADDED TO DIRECTORY</span><strong>{{ formatDate(selectedUser.createdAt) }}</strong><button class="delete-link" type="button" @click="removeUser(selectedUser)"><Trash2 :size="14" /> Delete profile</button></div>
            </template>
            <div v-else class="detail-empty"><span class="detail-empty-mark"><UsersRound :size="22" /></span><strong>Your directory starts here</strong><p>Add a profile to keep the important details close.</p><button class="small-primary-button" type="button" @click="openCreate"><Plus :size="15" /> Add person</button></div>
          </aside>
        </div>
        <footer class="page-footer"><span>FIELDNOTE <i>•</i> PEOPLE DIRECTORY</span><span>Made for the people who make it work.</span></footer>
      </section>
    </main>

    <Transition name="toast"><div v-if="notice" class="toast-message" role="status"><Check :size="16" /> {{ notice }}</div></Transition>

    <Transition name="modal">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal" @keydown.esc="closeModal">
        <section class="profile-modal" role="dialog" aria-modal="true" :aria-labelledby="'modal-title'">
          <header class="modal-header"><div><span class="modal-kicker">PROFILE DETAILS</span><h2 id="modal-title">{{ editingId ? 'Edit profile' : 'Add a person' }}</h2></div><button class="icon-button" type="button" aria-label="Close" @click="closeModal"><X :size="18" /></button></header>
          <form class="profile-form" @submit.prevent="saveUser">
            <div class="form-intro"><span class="form-avatar"><UserRound :size="20" /></span><span><strong>{{ editingId ? 'Keep their details current.' : 'Make room for someone new.' }}</strong><small>Fields marked with * are required.</small></span></div>
            <div class="form-grid">
              <label class="field"><span>First name <b>*</b></span><input v-model="form.firstName" required maxlength="100" autocomplete="given-name" placeholder="e.g. Jamie" /></label>
              <label class="field"><span>Last name <b>*</b></span><input v-model="form.lastName" required maxlength="100" autocomplete="family-name" placeholder="e.g. Chen" /></label>
              <label class="field full"><span>Email address <b>*</b></span><input v-model="form.email" required type="email" maxlength="320" autocomplete="email" placeholder="jamie@company.com" /></label>
              <label class="field full"><span>Phone number</span><input v-model="form.phone" type="tel" maxlength="32" autocomplete="tel" placeholder="+1 (555) 000-0000" /></label>
              <label class="field full"><span>About them</span><textarea v-model="form.bio" rows="3" placeholder="A little about what they do..." /></label>
              <label class="field full"><span>Avatar image URL</span><input v-model="form.avatarUrl" type="url" placeholder="https://example.com/photo.jpg" /></label>
            </div>
            <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
            <footer class="modal-footer"><button class="cancel-button" type="button" :disabled="saving" @click="closeModal">Cancel</button><button class="primary-button" type="submit" :disabled="saving"><LoaderCircle v-if="saving" class="spin" :size="16" /><Check v-else :size="16" /> {{ saving ? 'Saving...' : editingId ? 'Save changes' : 'Create profile' }}</button></footer>
          </form>
        </section>
      </div>
    </Transition>
  </div>
</template>