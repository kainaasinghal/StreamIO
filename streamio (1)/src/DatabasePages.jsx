import React, { useEffect, useState } from 'react';
import {
  createRecord,
  deleteRecord,
  getApiHealth,
  getCollection,
  getDashboard,
  getOptions,
  updateRecord,
} from './api';

const pages = {
  users: {
    resource: 'users', title: 'Users', eyebrow: 'Audience / Directory', copy: 'Manage member accounts and their current subscription.',
    columns: [['name', 'Member'], ['email', 'Email'], ['plan_name', 'Plan'], ['subscription_status', 'Subscription'], ['country', 'Country']],
    fields: [
      { name: 'name', label: 'Full name', required: true }, { name: 'email', label: 'Email address', type: 'email', required: true },
      { name: 'phone', label: 'Phone', maxLength: 15 }, { name: 'country', label: 'Country', maxLength: 50 },
      { name: 'plan_id', label: 'Subscription plan', type: 'options', optionGroup: 'plans', optionLabel: 'plan_name', optionValue: 'plan_id', optionPrice: true, optional: true },
    ],
    filters: [{ name: 'status', label: 'All subscriptions', options: [['active', 'Active'], ['expired', 'Expired'], ['cancelled', 'Cancelled'], ['unsubscribed', 'No subscription']] }],
    sortFields: [['user_id', 'ID'], ['name', 'Name'], ['email', 'Email'], ['country', 'Country']],
    search: 'Search names, emails, or countries',
  },
  content: {
    resource: 'content', title: 'Content', eyebrow: 'Library / Catalog', copy: 'Manage titles, release metadata, and category links.',
    columns: [['title', 'Title'], ['category_name', 'Category'], ['release_year', 'Year'], ['duration', 'Minutes'], ['rating', 'Editorial rating'], ['average_review_rating', 'Review average'], ['watch_count', 'Plays']],
    fields: [
      { name: 'title', label: 'Title', required: true }, { name: 'release_year', label: 'Release year', type: 'number', min: 1901, max: 2155 },
      { name: 'duration', label: 'Duration (minutes)', type: 'number', min: 1 }, { name: 'rating', label: 'Editorial rating (0-10)', type: 'number', min: 0, max: 10, step: 0.1 },
      { name: 'language', label: 'Language', maxLength: 30 }, { name: 'category_id', label: 'Category', type: 'options', optionGroup: 'categories', optionLabel: 'category_name', optionValue: 'category_id', optional: true },
    ],
    filters: [{ name: 'category_id', label: 'All categories', optionGroup: 'categories', optionLabel: 'category_name', optionValue: 'category_id' }],
    sortFields: [['content_id', 'ID'], ['title', 'Title'], ['release_year', 'Release year'], ['rating', 'Editorial rating']],
    search: 'Search titles or languages',
  },
  subscription: {
    resource: 'subscriptions', title: 'Subscription', eyebrow: 'Growth / Memberships', copy: 'Review membership periods, plan assignments, and status.',
    columns: [['user_name', 'Member'], ['plan_name', 'Plan'], ['price', 'Plan price'], ['start_date', 'Started'], ['end_date', 'Ends'], ['status', 'Status']],
    fields: [
      { name: 'user_id', label: 'Member', type: 'options', optionGroup: 'users', optionLabel: 'name', optionValue: 'user_id', required: true },
      { name: 'plan_id', label: 'Subscription plan', type: 'options', optionGroup: 'plans', optionLabel: 'plan_name', optionValue: 'plan_id', optionPrice: true, required: true },
      { name: 'price', label: 'Price from plan', type: 'number', min: 0, step: 0.01, money: true, readOnly: true, displayOnly: true, required: true },
      { name: 'start_date', label: 'Start date', type: 'date', required: true }, { name: 'end_date', label: 'End date', type: 'date', optional: true },
      { name: 'status', label: 'Status', type: 'select', options: [['active', 'Active'], ['expired', 'Expired'], ['cancelled', 'Cancelled']] },
    ],
    filters: [{ name: 'status', label: 'All statuses', options: [['active', 'Active'], ['expired', 'Expired'], ['cancelled', 'Cancelled']] }, { name: 'plan_id', label: 'All plans', optionGroup: 'plans', optionLabel: 'plan_name', optionValue: 'plan_id' }],
    sortFields: [['subscription_id', 'ID'], ['start_date', 'Start date'], ['status', 'Status']],
    search: 'Search members or plans',
  },
  payment: {
    resource: 'payments', title: 'Payment History', eyebrow: 'Finance / Transactions', copy: 'Track imported transactions and their subscription owners.',
    columns: [['payment_date', 'Date'], ['user_name', 'Member'], ['plan_name', 'Plan'], ['payment_amount', 'Amount'], ['payment_method', 'Method'], ['status', 'Status']],
    fields: [
      { name: 'payment_date', label: 'Payment date', type: 'date', required: true }, { name: 'payment_amount', label: 'Amount', type: 'number', min: 0, step: 0.01, money: true, required: true },
      { name: 'payment_method', label: 'Method', maxLength: 30 }, { name: 'status', label: 'Status', type: 'select', options: [['success', 'Successful'], ['failed', 'Failed'], ['refunded', 'Refunded']] },
      { name: 'subscription_id', label: 'Subscription', type: 'options', optionGroup: 'subscriptions', optionLabel: 'label', optionValue: 'subscription_id', required: true },
    ],
    filters: [{ name: 'status', label: 'All statuses', options: [['success', 'Successful'], ['failed', 'Failed'], ['refunded', 'Refunded']] }],
    sortFields: [['payment_number', 'ID'], ['payment_date', 'Date'], ['payment_amount', 'Amount'], ['status', 'Status']],
    search: 'Search members, plans, or methods',
  },
  history: {
    resource: 'watch-history', title: 'Watch History', eyebrow: 'Audience / Engagement', copy: 'See imported viewing dates, completion, and estimated minutes watched.',
    columns: [['user_name', 'Member'], ['content_title', 'Title'], ['category_name', 'Category'], ['watch_date', 'Date'], ['watch_time', 'Time'], ['progress', 'Progress'], ['completed', 'Completed'], ['watched_minutes', 'Est. minutes']],
    fields: [
      { name: 'user_id', label: 'Member', type: 'options', optionGroup: 'users', optionLabel: 'name', optionValue: 'user_id', required: true },
      { name: 'content_id', label: 'Content', type: 'options', optionGroup: 'content', optionLabel: 'title', optionValue: 'content_id', required: true },
      { name: 'watch_date', label: 'Watch date', type: 'date', required: true }, { name: 'watch_time', label: 'Watch time', type: 'time', optional: true },
      { name: 'progress', label: 'Progress (%)', type: 'number', min: 0, max: 100, step: 0.01 }, { name: 'completed', label: 'Completed', type: 'checkbox' },
    ],
    filters: [{ name: 'status', label: 'All viewing states', options: [['completed', 'Completed'], ['in-progress', 'In progress']] }],
    sortFields: [['history_id', 'ID'], ['watch_date', 'Date'], ['progress', 'Progress']],
    search: 'Search members or titles',
  },
  reviews: {
    resource: 'reviews', title: 'Reviews', eyebrow: 'Audience / Voice', copy: 'Manage audience ratings and comments from the dataset.',
    columns: [['user_name', 'Member'], ['content_title', 'Title'], ['rating', 'Rating / 10'], ['comment', 'Comment'], ['review_date', 'Date']],
    fields: [
      { name: 'user_id', label: 'Member', type: 'options', optionGroup: 'users', optionLabel: 'name', optionValue: 'user_id', required: true },
      { name: 'content_id', label: 'Content', type: 'options', optionGroup: 'content', optionLabel: 'title', optionValue: 'content_id', required: true },
      { name: 'rating', label: 'Rating (0-10)', type: 'number', min: 0, max: 10, step: 0.1, required: true },
      { name: 'comment', label: 'Comment', type: 'textarea', maxLength: 500 }, { name: 'review_date', label: 'Review date', type: 'date', required: true },
    ],
    filters: [], sortFields: [['review_id', 'ID'], ['review_date', 'Date'], ['rating', 'Rating']], search: 'Search member, title, or comment',
  },
};

const planFormPage = {
  resource: 'plans',
  title: 'plan',
  fields: [
    { name: 'plan_name', label: 'Plan name', required: true, maxLength: 50 },
    { name: 'price', label: 'Price', type: 'number', min: 0, step: 0.01, money: true, required: true },
    { name: 'duration_months', label: 'Duration (months)', type: 'number', min: 1, required: true },
  ],
};

function today() {
  return new Date().toISOString().slice(0, 10);
}

function initialForm(page, record) {
  const form = {};
  page.fields.forEach(field => {
    let value = record?.[field.name];
    if (!record && field.name === 'status') value = page.resource === 'payments' ? 'success' : 'active';
    if (field.name === 'plan_id' && page.resource === 'users' && value == null) value = '';
    if (field.type === 'date' && !value && field.required) value = today();
    if (field.type === 'checkbox') value = Boolean(value);
    form[field.name] = value ?? '';
  });
  return form;
}

function recordPayload(page, form) {
  const payload = {};
  page.fields.forEach(field => {
    if (field.displayOnly) return;
    const value = form[field.name];
    if ((value === '' || value == null) && field.optional) return;
    if (field.type === 'checkbox') payload[field.name] = Boolean(value);
    else if (field.money) payload[field.name] = String(value ?? '');
    else if (field.type === 'number' || field.type === 'options') payload[field.name] = value === '' ? null : Number(value);
    else payload[field.name] = value === '' ? null : value;
  });
  return payload;
}

function validateForm(page, form, options) {
  const errors = {};
  page.fields.forEach(field => {
    const value = form[field.name];
    const empty = value == null || String(value).trim() === '';
    if (field.required && empty) {
      errors[field.name] = field.type === 'options'
        ? `Please select ${field.label.toLowerCase()}.`
        : `Please enter ${field.label.toLowerCase()}.`;
      return;
    }
    if (empty) return;
    if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value))) {
      errors[field.name] = 'Please enter a valid email address.';
      return;
    }
    if (field.type === 'number' || field.money) {
      const numeric = Number(value);
      if (!Number.isFinite(numeric)) errors[field.name] = 'Please enter a valid number.';
      else if (field.min !== undefined && numeric < field.min) errors[field.name] = field.name === 'payment_amount' ? 'Payment amount must be greater than or equal to zero.' : field.money || field.name === 'price' ? 'Price must be greater than or equal to zero.' : `${field.label} must be at least ${field.min}.`;
      else if (field.max !== undefined && numeric > field.max) errors[field.name] = `${field.label} must be no greater than ${field.max}.`;
      return;
    }
    if (field.type === 'options') {
      const available = options[field.optionGroup] || [];
      const optionValue = field.optionValue || `${field.optionGroup.slice(0, -1)}_id`;
      if (!available.some(option => String(option[optionValue]) === String(value))) {
        errors[field.name] = `Please select a valid ${field.label.toLowerCase()}.`;
      }
    }
  });
  if (page.resource === 'subscriptions' && form.start_date && form.end_date && form.end_date < form.start_date) {
    errors.end_date = 'End date cannot be earlier than start date.';
  }
  return errors;
}

function InputField({ field, value, onChange, options, error }) {
  if (field.type === 'select' || field.type === 'options') {
    const values = field.type === 'select'
      ? field.options.map(([optionValue, label]) => ({ value: optionValue, label }))
      : (options[field.optionGroup] || []).map(item => ({
        value: item[field.optionValue || field.optionGroup.slice(0, -1) + '_id'],
        label: `${item[field.optionLabel]}${field.optionPrice ? ` · ${Number(item.price).toFixed(2)}` : ''}`,
      }));
    return <label className="field"><span>{field.label}{field.required && <b className="required-marker"> *</b>}</span><select required={field.required} disabled={field.required && values.length === 0} aria-invalid={Boolean(error)} value={value} onChange={event => onChange(event.target.value)}>
      <option value="" disabled={field.required}>{field.optional ? 'None' : values.length ? 'Select an option' : 'No options available'}</option>{values.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
    </select>{field.hint && <small className="field-hint">{field.hint}</small>}{field.type === 'options' && field.required && values.length === 0 && <small className="field-hint">No {field.label.toLowerCase()} records are available. Add one before saving.</small>}{error && <small className="field-error">{error}</small>}</label>;
  }
  if (field.type === 'checkbox') return <label className="field checkbox-field"><span>{field.label}</span><input type="checkbox" checked={Boolean(value)} onChange={event => onChange(event.target.checked)} />{error && <small className="field-error">{error}</small>}</label>;
  const common = { required: field.required, maxLength: field.maxLength, min: field.min, max: field.max, step: field.step, readOnly: field.readOnly, 'aria-invalid': Boolean(error), value, onChange: event => onChange(event.target.value) };
  return <label className="field"><span>{field.label}{field.required && <b className="required-marker"> *</b>}</span>{field.type === 'textarea' ? <textarea {...common} rows="4" /> : <input {...common} type={field.type || 'text'} />}{error && <small className="field-error">{error}</small>}</label>;
}

function EditModal({ page, record, options, onClose, onSave, onDelete }) {
  const formPage = record && page.resource === 'subscriptions' && record.plan_id == null
    ? { ...page, fields: page.fields.map(field => field.name === 'plan_id' ? { ...field, required: false, optional: true, hint: `The saved plan snapshot (${record.plan_name} · ${Number(record.price).toFixed(2)}) has no matching plan in the catalog and will be preserved.` } : field) }
    : record && page.resource === 'users' && record.plan_id == null && record.plan_name
      ? { ...page, fields: page.fields.map(field => field.name === 'plan_id' ? { ...field, hint: `Current subscription snapshot: ${record.plan_name}. No matching plan catalog row is available; the saved subscription will be preserved.` } : field) }
    : page;
  const [form, setForm] = useState(() => initialForm(formPage, record));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const remove = async () => {
    setSaving(true);
    setError('');
    setFieldErrors({});
    try {
      const deleted = await onDelete();
      if (deleted !== false) onClose();
    } catch (reason) {
      setError(reason.message);
      setFieldErrors(reason.fieldErrors || {});
    } finally {
      setSaving(false);
    }
  };
  const save = async event => {
    event.preventDefault();
    const validationErrors = validateForm(formPage, form, options);
    setFieldErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;
    setSaving(true);
    setError('');
    try {
      await onSave(recordPayload(formPage, form));
      onClose();
    } catch (reason) {
      setError(reason.message);
      setFieldErrors(reason.fieldErrors || {});
    } finally {
      setSaving(false);
    }
  };
  return <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && onClose()}><form className="modal" noValidate onSubmit={save}>
    <div className="modal-head"><div><h2>{record ? `Edit ${page.title}` : `Add ${page.title}`}</h2><p>Changes are saved to the MySQL database.</p></div><button className="close-button" type="button" onClick={onClose}>×</button></div>
    <div className="modal-form">{formPage.fields.map(field => <InputField key={field.name} field={field} value={form[field.name]} options={options} error={fieldErrors[field.name]} onChange={value => setForm(current => ({ ...current, [field.name]: value, ...(field.optionPrice ? { price: options.plans.find(plan => String(plan.plan_id) === String(value))?.price ?? '' } : {}) }))} />)}</div>
    {error && <p className="api-error" role="alert">{error}</p>}
    <div className="modal-actions">{record && <button className="button button-danger" type="button" disabled={saving} onClick={remove}>Delete</button>}<button className="button button-ghost" type="button" onClick={onClose}>Cancel</button><button className="button button-primary" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button></div>
  </form></div>;
}

function displayValue(key, value) {
  if (value == null || value === '') return '—';
  if (key === 'completed') return value ? 'Yes' : 'No';
  if (key === 'payment_amount' || key === 'price') return Number(value).toFixed(2);
  if (key === 'rating' || key === 'average_review_rating' || key === 'progress' || key === 'watched_minutes') return Number(value).toFixed(key === 'watched_minutes' ? 1 : 1);
  return String(value);
}

function DatabasePage({ pageKey, showToast }) {
  const page = pages[pageKey];
  const [options, setOptions] = useState({ plans: [], categories: [], users: [], subscriptions: [], content: [] });
  const [result, setResult] = useState({ items: [], total: 0 });
  const [query, setQuery] = useState('');
  const [filterValues, setFilterValues] = useState({});
  const [sortBy, setSortBy] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [pageNumber, setPageNumber] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [record, setRecord] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [planModalOpen, setPlanModalOpen] = useState(false);
  const [pageOptionsError, setPageOptionsError] = useState('');
  const [pageSize, setPageSize] = useState(8);

  useEffect(() => {
    getOptions().then(value => setOptions(current => ({ ...current, ...value }))).catch(reason => setPageOptionsError(reason.message));
  }, []);

  useEffect(() => {
    let current = true;
    setLoading(true);
    setError('');
    getCollection(page.resource, { q: query, page: pageNumber, page_size: pageSize, sort_by: sortBy, descending: sortDirection === 'desc', ...filterValues })
      .then(value => { if (current) setResult(value); })
      .catch(reason => { if (current) setError(reason.message); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [page.resource, query, filterValues, pageNumber, pageSize, refreshKey, sortBy, sortDirection]);

  useEffect(() => {
    const lastPage = Math.max(1, Math.ceil(result.total / pageSize));
    if (pageNumber > lastPage) setPageNumber(lastPage);
  }, [result.total, pageSize, pageNumber]);

  const save = async payload => {
    if (record) {
      await updateRecord(page.resource, record[pageKey === 'payment' ? 'payment_number' : pageKey === 'history' ? 'history_id' : pageKey === 'subscription' ? 'subscription_id' : pageKey === 'content' ? 'content_id' : pageKey === 'reviews' ? 'review_id' : 'user_id'], payload);
    } else {
      await createRecord(page.resource, payload);
      setQuery('');
      setFilterValues({});
      setSortBy('');
      setSortDirection('asc');
      const refreshed = await getCollection(page.resource, { page: 1, page_size: 1 });
      setPageNumber(Math.max(1, Math.ceil(refreshed.total / pageSize)));
    }
    setRefreshKey(value => value + 1);
    showToast(record ? 'Record updated in the database' : 'Record created in the database');
  };

  const remove = async () => {
    const key = pageKey === 'payment' ? 'payment_number' : pageKey === 'history' ? 'history_id' : pageKey === 'subscription' ? 'subscription_id' : pageKey === 'content' ? 'content_id' : pageKey === 'reviews' ? 'review_id' : 'user_id';
    if (!window.confirm(`Delete this ${page.title.toLowerCase()} record? Related rows follow the database foreign-key rules.`)) return false;
    await deleteRecord(page.resource, record[key]);
    setModalOpen(false);
    setRefreshKey(value => value + 1);
    showToast('Record deleted from the database');
  };

  const savePlan = async payload => {
    await createRecord('plans', payload);
    try {
      setOptions(await getOptions());
      setPageOptionsError('');
    } catch (reason) {
      setPageOptionsError(reason.message);
    }
    showToast('Plan added to the database catalog');
  };

  const totalPages = Math.max(1, Math.ceil(result.total / pageSize));
  const exportCsv = () => {
    if (!result.items.length) {
      showToast('There are no rows to export');
      return;
    }
    const escape = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
    const lines = [
      page.columns.map(([, label]) => escape(label)).join(','),
      ...result.items.map(item => page.columns.map(([key]) => escape(item[key])).join(',')),
    ];
    const link = document.createElement('a');
    const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8' }));
    link.href = url;
    link.download = `${page.resource}-${today()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`Exported ${result.items.length} rows from this page`);
  };
  return <div className={`page-enter pdf-page ${pageKey}-page`}>
    <header className="page-header"><div><span className="eyebrow">{page.eyebrow}</span><h1>{page.title}</h1><p>{page.copy}</p></div><button className="button button-primary" onClick={() => { setRecord(null); setModalOpen(true); }}>＋ Add record</button></header>
    {pageOptionsError && <p className="api-error" role="alert">Related options could not load: {pageOptionsError}</p>}
    <div className="toolbar-row table-toolbar"><label className="search-field"><span aria-hidden="true">⌕</span><input value={query} onChange={event => { setQuery(event.target.value); setPageNumber(1); }} placeholder={page.search} /></label>
      {page.filters.map(filter => <label className="select-wrap" key={filter.name}><select value={filterValues[filter.name] || ''} onChange={event => { setPageNumber(1); setFilterValues(current => ({ ...current, [filter.name]: event.target.value })); }}>
        <option value="">{filter.label}</option>{filter.options ? filter.options.map(([value, label]) => <option key={value} value={value}>{label}</option>) : (options[filter.optionGroup] || []).map(option => <option key={option[filter.optionValue]} value={option[filter.optionValue]}>{option[filter.optionLabel]}</option>)}
      </select></label>)}
      <label className="select-wrap"><select aria-label="Sort records by" value={sortBy} onChange={event => { setPageNumber(1); setSortBy(event.target.value); }}><option value="">Default order</option>{page.sortFields.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="select-wrap"><select aria-label="Sort direction" value={sortDirection} onChange={event => { setPageNumber(1); setSortDirection(event.target.value); }}><option value="asc">Ascending</option><option value="desc">Descending</option></select></label>
      <label className="select-wrap"><select aria-label="Rows per page" value={pageSize} onChange={event => { setPageNumber(1); setPageSize(Number(event.target.value)); }}><option value={2}>2 rows</option><option value={8}>8 rows</option><option value={20}>20 rows</option><option value={50}>50 rows</option></select></label>
      {pageKey === 'subscription' && <button className="button button-ghost" onClick={() => setPlanModalOpen(true)}>＋ Add plan</button>}
      <button className="button button-ghost" onClick={exportCsv}>Export CSV</button>
    </div>
    <section className="panel table-panel"><div className="panel-head"><div><span className="eyebrow">{result.total} records</span><h2>{page.title} records</h2></div><span className="table-meta">{loading ? 'Refreshing…' : 'MySQL-backed'}</span></div>
      {error ? <div className="api-error api-state" role="alert"><strong>Could not load records</strong><span>{error}</span><button className="button button-ghost" onClick={() => setRefreshKey(value => value + 1)}>Retry</button></div> : loading ? <div className="api-state" role="status">Loading records…</div> : result.items.length === 0 ? <div className="api-state">No matching records.</div> : <div className="table-shell"><table className={`data-table ${pageKey}-data-table`}><thead><tr>{page.columns.map(([, label]) => <th key={label}>{label}</th>)}<th /></tr></thead><tbody>{result.items.map(item => {
        const idKey = pageKey === 'payment' ? 'payment_number' : pageKey === 'history' ? 'history_id' : pageKey === 'subscription' ? 'subscription_id' : pageKey === 'content' ? 'content_id' : pageKey === 'reviews' ? 'review_id' : 'user_id';
        return <tr key={item[idKey]}>{page.columns.map(([key]) => <td key={key}>{key === 'name' || key === 'title' || key === 'user_name' || key === 'content_title' ? <strong>{displayValue(key, item[key])}</strong> : displayValue(key, item[key])}</td>)}<td><button className="row-action" aria-label={`Edit ${page.title} record`} onClick={() => { setRecord(item); setModalOpen(true); }}>•••</button></td></tr>;
      })}</tbody></table></div>}
      <div className="pagination"><span>Page {pageNumber} of {totalPages} · Showing {result.total ? (pageNumber - 1) * pageSize + 1 : 0}-{Math.min(pageNumber * pageSize, result.total)} of {result.total}</span><div><button disabled={pageNumber <= 1 || loading} onClick={() => setPageNumber(value => value - 1)}>Previous</button><button className="current" aria-current="page">{pageNumber}</button><button disabled={pageNumber >= totalPages || loading} onClick={() => setPageNumber(value => value + 1)}>Next</button></div></div>
    </section>
    {modalOpen && <EditModal page={page} record={record} options={options} onClose={() => setModalOpen(false)} onSave={save} onDelete={remove} />}
    {planModalOpen && <EditModal page={planFormPage} record={null} options={options} onClose={() => setPlanModalOpen(false)} onSave={savePlan} />}
  </div>;
}

function Metric({ label, value, tone = '' }) {
  return <article className={`stat-card ${tone}`}><div className="stat-top"><span>{label}</span></div><div className="stat-value">{value}</div><div className="stat-bottom"><span>From database records</span></div></article>;
}

function ConnectedDashboard({ setPage, showToast }) {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState('Checking database…');
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    getDashboard().then(value => { if (active) setStats(value); }).catch(reason => { if (active) setError(reason.message); });
    getApiHealth().then(value => { if (active) setHealth(value.database === 'connected' ? 'Database connected' : 'Database unavailable'); }).catch(() => { if (active) setHealth('Database unavailable'); });
    return () => { active = false; };
  }, []);
  const money = value => new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(Number(value || 0));
  return <div className="management-dashboard"><header className="cinema-header management-header"><a className="cinema-logo" href="#management-top"><span className="logo-mark"><i /><i /><i /></span><span>streamio</span></a><span className="ops-label">OPERATIONS CONSOLE</span><div className="cinema-admin-nav" aria-label="Admin pages">{['dashboard', 'users', 'content', 'subscription', 'payment', 'history', 'reviews'].map(key => <button key={key} className={key === 'dashboard' ? 'active' : ''} onClick={() => setPage(key)}>{key === 'payment' ? 'Payment History' : key === 'history' ? 'Watch History' : key[0].toUpperCase() + key.slice(1)}</button>)}</div><div className="cinema-actions"><span className="health-pill"><i />{health}</span></div></header>
    <main id="management-top" className="management-main"><section className="management-hero"><div className="management-hero-copy"><span className="cinema-eyebrow"><span><i /> Platform command</span><b>MYSQL / LIVE</b></span><h1>Your Platform.<br />Your <em>Control.</em></h1><p>Audience, catalog, revenue, and viewing activity, summarized from your MySQL records.</p><div className="management-meta"><span className="health-pill"><i />{health}</span><span>Schema · 9 relational tables</span></div></div><div className="management-hero-graphic"><div className="management-grid-lines" /><div className="management-orbit management-orbit-a" /><div className="management-orbit management-orbit-b" /><div className="management-core"><span>LIVE</span><strong>{stats ? stats.members : '—'}</strong><small>REGISTERED MEMBERS</small></div><div className="management-readout readout-a"><b>{stats ? stats.content : '—'}</b><span>catalog titles</span></div><div className="management-readout readout-b"><b>{stats ? stats.active_subscriptions : '—'}</b><span>active subscriptions</span></div><span className="graphic-code">STO / SQL<br />STREAMIO CONTROL</span><div className="management-beam beam-a" /><div className="management-beam beam-b" /><div className="management-scan" /></div></section>
      {error && <p className="api-error" role="alert">{error}</p>}
      {stats ? <><section className="stats-grid management-stats"><Metric label="Registered members" value={stats.members} tone="stat-cyan" /><Metric label="Catalog titles" value={stats.content} /><Metric label="Successful payment total" value={money(stats.successful_revenue)} tone="stat-amber" /><Metric label="Estimated watch time" value={`${Number(stats.watch_minutes).toLocaleString()} min`} tone="stat-cyan" /></section>
      <div className="dashboard-grid management-grid"><section className="panel management-chart-panel"><div className="panel-head"><div><span className="eyebrow">Finance / Database</span><h2>Successful payments by month</h2></div><span className="chart-note">{stats.payments} payment records</span></div><div className="db-month-chart">{stats.monthly_revenue.length ? stats.monthly_revenue.map(row => <div key={row.month} title={`${row.month}: ${money(row.revenue)}`}><i style={{ height: `${Math.max(6, Number(row.revenue) / Math.max(...stats.monthly_revenue.map(item => Number(item.revenue)), 1) * 100)}%` }} /><span>{row.month.slice(5)}</span></div>) : <p>No successful payments yet.</p>}</div></section>
        <section className="panel platform-pulse"><div className="panel-head"><div><span className="eyebrow">Ratings / Audience</span><h2>Review average</h2></div><span className="chart-note">{stats.review_count} reviews</span></div><div className="pulse-ring"><div><strong>{Number(stats.average_review_rating).toFixed(1)}</strong><span>out of 10</span></div></div><div className="pulse-list">{stats.subscriptions_by_plan.map(row => <span key={row.plan}><b>{row.plan}</b><i><em style={{ width: `${stats.active_subscriptions ? row.members / stats.active_subscriptions * 100 : 0}%` }} /></i><small>{row.members}</small></span>)}</div></section></div>
      <div className="dashboard-grid management-grid lower-grid"><section className="panel operations-panel"><div className="panel-head"><div><span className="eyebrow">Catalog intelligence</span><h2>Most watched titles</h2></div><button className="text-action" onClick={() => setPage('content')}>Open catalog <span>→</span></button></div><div className="operations-content-list">{stats.top_content.map((item, index) => <div className="operations-content-row" key={item.content_id}><span className="ops-rank">{String(index + 1).padStart(2, '0')}</span><div><strong>{item.title}</strong><span>{item.category_name || 'Uncategorized'} · {item.watch_count} plays</span></div><b>{Number(item.average_rating || 0).toFixed(1)} / 10</b></div>)}</div></section>
        <section className="panel activity-panel"><div className="panel-head"><div><span className="eyebrow">Dataset summary</span><h2>Records by category</h2></div><button className="icon-button" onClick={() => showToast('Dashboard data refreshed after reload')}>↻</button></div><div className="activity-feed">{stats.titles_by_category.slice(0, 5).map(item => <div key={item.category}><span className="feed-icon cyan">{item.titles}</span><p><b>{item.category}</b><span>{item.titles} catalog titles</span></p></div>)}</div></section></div></> : !error && <div className="api-state" role="status">Loading database summary…</div>}
    </main></div>;
}

export function DatabaseConsole({ pageKey, setPage, showToast }) {
  return pageKey === 'dashboard' ? <ConnectedDashboard setPage={setPage} showToast={showToast} /> : <DatabasePage key={pageKey} pageKey={pageKey} showToast={showToast} />;
}