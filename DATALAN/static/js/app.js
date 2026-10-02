document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('#sidebar');
  document.querySelector('[data-sidebar-toggle]')?.addEventListener('click', () => sidebar?.classList.toggle('open'));
  document.querySelectorAll('[data-password-toggle]').forEach((button) => button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.passwordToggle);
    input.type = input.type === 'password' ? 'text' : 'password';
    button.textContent = input.type === 'password' ? 'Mostrar' : 'Ocultar';
  }));
  document.querySelectorAll('[data-confirm]').forEach((form) => form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  }));
  const requestTabsContainer = document.querySelector('.request-tabs');
  if (requestTabsContainer) {
    document.querySelectorAll('.request-card .status-pill').forEach((pill) => {
      const statusClass = { PENDIENTE: 'pending', OBSERVADO: 'observed' }[pill.textContent.trim()];
      if (statusClass) {
        pill.classList.remove('process');
        pill.classList.add(statusClass);
      }
    });
    const pendingTab = document.createElement('a');
    pendingTab.className = `request-tab tab-pending${window.location.pathname === '/comercial/pendientes/' ? ' active' : ''}`;
    pendingTab.href = '/comercial/pendientes/';
    pendingTab.textContent = 'PENDIENTE';
    const tabsByClass = ['tab-all', 'tab-process', 'tab-approved', 'tab-rejected']
      .map((className) => requestTabsContainer.querySelector(`.${className}`));
    requestTabsContainer.querySelector('.tab-observed')?.remove();
    [tabsByClass[0], pendingTab, tabsByClass[1], tabsByClass[2], tabsByClass[3]]
      .filter(Boolean)
      .forEach((tab) => requestTabsContainer.appendChild(tab));
  }
  const requestTabs = document.querySelectorAll('.request-tabs .request-tab');
  const requestTabsScrollKey = 'commercial-request-tabs-scroll';
  const savedRequestTabsScroll = sessionStorage.getItem(requestTabsScrollKey);
  if (requestTabs.length && savedRequestTabsScroll !== null) {
    window.requestAnimationFrame(() => {
      window.scrollTo(0, Number(savedRequestTabsScroll));
      sessionStorage.removeItem(requestTabsScrollKey);
    });
  }
  requestTabs.forEach((tab) => tab.addEventListener('click', () => {
    sessionStorage.setItem(requestTabsScrollKey, String(window.scrollY));
  }));
  document.querySelectorAll('.toast').forEach((toast) => setTimeout(() => toast.remove(), 4200));
  const commercialStats = document.querySelector('.commercial-status-stats');
  if (commercialStats && !commercialStats.querySelector('a[href="/comercial/en-proceso/"]')) {
    const processCount = document.querySelectorAll('.commercial-table .status-pill.process').length;
    const processCard = document.createElement('a');
    processCard.className = 'stat-card status-link';
    processCard.href = '/comercial/en-proceso/';
    processCard.dataset.processCard = 'true';
    processCard.innerHTML = `<span class="card-label">Solicitudes en proceso</span><strong>${processCount}</strong><span>Ver detalle</span>`;
    commercialStats.insertBefore(processCard, commercialStats.firstElementChild);
  }
  if (window.location.pathname === '/comercial/en-proceso/') {
    document.querySelector('.request-cards')?.closest('.panel')?.querySelector('h2')?.replaceChildren(document.createTextNode('SOLICITUDES EN PROCESO'));
  }
  if (window.location.pathname === '/comercial/pendientes/') {
    document.querySelector('.request-cards')?.closest('.panel')?.querySelector('h2')?.replaceChildren(document.createTextNode('SOLICITUDES PENDIENTES'));
  }
  const detailStatus = {'/comercial/en-proceso/': 'EN PROCESO', '/comercial/aprobadas/': 'APROBADO', '/comercial/rechazadas/': 'RECHAZADO', '/comercial/observadas/': 'OBSERVADO'}[window.location.pathname];
  if (detailStatus) document.querySelectorAll('.request-card .status-pill').forEach((pill) => {
    pill.textContent = detailStatus;
    pill.className = `status-pill ${detailStatus === 'APROBADO' ? 'success' : detailStatus === 'RECHAZADO' ? 'danger' : 'process'}`;
  });

  const requestForm = document.querySelector('#commercial-request-form');
  if (requestForm) {
    requestForm.querySelector('#multipoint')?.remove();
    const locationPicker = createLocationPicker(requestForm);
    const applicantChoices = requestForm.querySelectorAll('input[name="applicant_kind"]');
    const applicantFields = requestForm.querySelector('.choice-row + .form-grid');
    const applicantInputs = applicantFields?.querySelectorAll('input') || [];
    const applicantLabels = applicantFields?.querySelectorAll('label') || [];
    const updateApplicant = (kind) => {
      const isEntity = kind === 'ENTIDAD';
      applicantFields.hidden = !kind;
      applicantInputs.forEach((input, index) => {
        input.disabled = !kind;
        input.required = Boolean(kind) && index < 2;
      });
      if (applicantLabels.length >= 3) {
        applicantLabels[0].childNodes[0].textContent = isEntity ? 'Empresa ' : 'Nombre del solicitante ';
        applicantLabels[2].childNodes[0].textContent = isEntity ? 'Nombre asociado ' : 'Entidad o empresa asociada ';
      }
    };
    applicantChoices.forEach((choice) => {
      choice.checked = false;
      choice.addEventListener('change', () => updateApplicant(choice.value));
    });
    updateApplicant('');
    const typeSelect = requestForm.querySelector('#request-type');
    const pointToPoint = requestForm.querySelector('#point-to-point');
    const equipmentToggle = requestForm.querySelector('[data-equipment-toggle]');
    const equipmentFields = requestForm.querySelector('[data-equipment-fields]');
    const equipmentLine = requestForm.querySelector('.equipment-toggle');
    if (equipmentToggle && equipmentLine && !requestForm.querySelector('.equipment-choice-row')) {
      const equipmentChoices = document.createElement('div');
      equipmentChoices.className = 'choice-row equipment-choice-row';
      equipmentChoices.innerHTML = '<label class="choice"><input type="radio" name="equipment_choice" value="SIN EQUIPO"><span>SIN EQUIPO</span></label><label class="choice"><input type="radio" name="equipment_choice" value="CON EQUIPO"><span>CON EQUIPO</span></label>';
      const equipmentParent = equipmentLine.parentNode;
      equipmentLine.remove();
      equipmentParent.insertBefore(equipmentChoices, equipmentFields);
      equipmentChoices.querySelectorAll('input').forEach((choice) => choice.addEventListener('change', () => {
        const withEquipment = choice.value === 'CON EQUIPO';
        if (choice.checked) {
          equipmentToggle.checked = withEquipment;
          equipmentFields.hidden = !withEquipment;
        }
      }));
    }
    const updateType = () => {
      const isMultipoint = typeSelect.value === 'Instalación Punto Multipunto';
      pointToPoint.hidden = false;
      requestForm.querySelectorAll('[data-location-group="origin"]').forEach((group) => {
        group.hidden = isMultipoint;
        group.style.display = isMultipoint ? 'none' : '';
      });
      requestForm.querySelectorAll('[name="origin"], [name="origin_location"], [name="origin_coordinates"]').forEach((input) => {
        input.required = !isMultipoint;
        input.disabled = isMultipoint;
        if (!input.closest('[data-location-group="origin"]')) {
          const field = input.closest('.field');
          field.hidden = isMultipoint;
          field.style.display = isMultipoint ? 'none' : '';
        }
      });
      requestForm.querySelectorAll('[name="destination"], [name="destination_location"], [name="destination_coordinates"]').forEach((input) => { input.required = true; });
    };
    typeSelect.addEventListener('change', updateType);
    equipmentToggle.addEventListener('change', () => { equipmentFields.hidden = !equipmentToggle.checked; });
    requestForm.addEventListener('submit', (event) => {
      if (!requestForm.checkValidity()) {
        event.preventDefault();
        requestForm.reportValidity();
      }
    });
    requestForm.addEventListener('reset', () => {
      window.setTimeout(() => {
        updateType();
        equipmentFields.hidden = true;
        locationPicker?.reset();
      });
    });
    updateType();
    const editDataElement = document.getElementById('commercial-request-edit-data');
    if (editDataElement) {
      const editingRequest = JSON.parse(editDataElement.textContent);
      const editCite = document.createElement('input');
      editCite.type = 'hidden';
      editCite.name = 'edit_cite';
      editCite.value = editingRequest.cite;
      requestForm.appendChild(editCite);
      const cancelButton = requestForm.querySelector('[type="reset"]');
      cancelButton.type = 'button';
      cancelButton.addEventListener('click', () => { window.location.assign('/comercial/pendientes/'); });
      const applicantKind = editingRequest.applicant_kind || 'CLIENTE';
      applicantChoices.forEach((choice) => { choice.checked = choice.value === applicantKind; });
      updateApplicant(applicantKind);
      typeSelect.value = editingRequest.type || '';
      updateType();
      ['applicant', 'email', 'company', 'priority', 'origin', 'origin_location', 'origin_coordinates', 'destination', 'destination_location', 'destination_coordinates', 'installation', 'installation_location', 'installation_coordinates', 'speed', 'equipment_type', 'requirements'].forEach((name) => {
        const field = requestForm.elements.namedItem(name);
        if (field) field.value = editingRequest[name] || '';
      });
      equipmentToggle.checked = Boolean(editingRequest.equipment_enabled);
      equipmentFields.hidden = !equipmentToggle.checked;
      const equipmentChoice = requestForm.querySelector(`[name="equipment_choice"][value="${equipmentToggle.checked ? 'CON EQUIPO' : 'SIN EQUIPO'}"]`);
      if (equipmentChoice) equipmentChoice.checked = true;
      requestForm.querySelector('[type="submit"]').textContent = 'Guardar cambios';
      requestForm.closest('.form-panel').querySelector('h2').textContent = 'Editar solicitud';
      document.querySelector('.heading h1').textContent = 'Editar solicitud';
    }
  }
  initializeRequestDetails();
  initializePlantRequests();
  initializeSystemsRequests();
});

function initializeRequestDetails() {
  const modal = document.querySelector('[data-request-modal]');
  if (!modal) return;
  const details = modal.querySelector('[data-modal-details]');
  const value = (card, key) => card.querySelector(`[data-detail="${key}"]`)?.textContent.trim() || '-';
  const statusClass = (status) => status === 'APROBADO' ? 'success' : status === 'RECHAZADO' ? 'danger' : status === 'OBSERVADO' ? 'observed' : 'process';
  const setStatus = (element, status) => { element.textContent = status; element.className = `approval-status ${statusClass(status)}`; };
  const close = () => { modal.hidden = true; document.body.classList.remove('modal-open'); };
  const actions = modal.querySelector('.request-modal-actions');
  const editLink = modal.querySelector('[data-modal-edit]');
  editLink.textContent = 'EDITAR';
  const rejectButton = modal.querySelector('[data-modal-reject]');
  const forwardLink = document.createElement('a');
  forwardLink.className = 'button';
  forwardLink.textContent = 'DERIVAR';
  actions.prepend(forwardLink);
  const cancelButton = document.createElement('button');
  cancelButton.type = 'button';
  cancelButton.className = 'button danger-button';
  cancelButton.textContent = 'CANCELAR';
  actions.appendChild(cancelButton);
  const csrfToken = () => modal.querySelector('[name="csrfmiddlewaretoken"]')?.value || decodeURIComponent(document.cookie.split('; ').find((row) => row.startsWith('csrftoken='))?.split('=')[1] || '');
  const postAction = (url, fields) => {
    const form = document.createElement('form');
    form.method = 'post';
    form.action = url;
    Object.entries({ ...fields, csrfmiddlewaretoken: csrfToken() }).forEach(([name, value]) => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      input.value = value;
      form.appendChild(input);
    });
    document.body.appendChild(form);
    form.submit();
  };
  const open = (card) => {
    const cite = card.dataset.requestCite;
    const requestStatus = card.querySelector('.status-pill')?.textContent.trim();
    const isPending = requestStatus === 'PENDIENTE';
    const canReject = !['PENDIENTE', 'EN PROCESO'].includes(requestStatus);
    const isMultipoint = value(card, 'type') === 'Instalación Punto Multipunto';
    const detailValue = (key) => {
      const current = value(card, key);
      if (!isMultipoint || current !== '-') return current;
      const legacyField = { destination: 'installation', 'destination-location': 'installation-location', 'destination-coordinates': 'installation-coordinates' }[key];
      return legacyField ? value(card, legacyField) : current;
    };
    modal.querySelector('[data-modal-cite]').textContent = cite;
    const requestFields = [['Solicitante','applicant'],['Tipo de solicitante','applicant-kind'],['Correo','email'],['Empresa','company'],['Tipo de solicitud','type'],['Prioridad','priority'],...(isMultipoint ? [] : [['PUNTO ORIGEN','origin'],['UBICACION ORIGEN','origin-location']]),['PUNTO DESTINO','destination'],['UBICACION DESTINO','destination-location'],...(!isMultipoint ? [['COORDENADA ORIGEN','origin-coordinates']] : []),['COORDENADA DESTINO','destination-coordinates'],...(!isMultipoint ? [['Punto de instalación','installation'],['Ubicación de instalación','installation-location'],['Coordenada de instalación','installation-coordinates']] : []),['Con equipo','equipment-enabled'],['Velocidad','speed'],['Tipo de equipo','equipment-type'],['Requisitos','requirements']];
    details.innerHTML = requestFields.map(([label, key]) => [label, detailValue(key)])
      .filter(([, fieldValue]) => fieldValue && fieldValue !== '-')
      .map(([label, fieldValue]) => `<div><b>${label}</b><span>${fieldValue}</span></div>`).join('');
    setStatus(modal.querySelector('[data-modal-plant-status]'), value(card, 'plant-status'));
    setStatus(modal.querySelector('[data-modal-systems-status]'), value(card, 'systems-status'));
    modal.querySelector('[data-modal-plant-user]').textContent = `Aprobó/revisó: ${value(card, 'plant-user')}`;
    modal.querySelector('[data-modal-systems-user]').textContent = `Aprobó/revisó: ${value(card, 'systems-user')}`;
    const approvalTitle = modal.querySelector('.approval-title');
    const approvalGrid = modal.querySelector('.approval-grid');
    approvalTitle.hidden = isPending;
    approvalTitle.style.display = isPending ? 'none' : '';
    approvalGrid.hidden = isPending;
    approvalGrid.style.display = isPending ? 'none' : '';
    editLink.href = `/comercial/solicitudes/nueva/?edit_cite=${encodeURIComponent(cite)}`;
    editLink.hidden = !isPending;
    editLink.style.display = isPending ? '' : 'none';
    forwardLink.href = `/comercial/solicitudes/derivar/${encodeURIComponent(cite)}/`;
    forwardLink.hidden = !isPending;
    forwardLink.style.display = isPending ? '' : 'none';
    cancelButton.hidden = !isPending;
    cancelButton.style.display = isPending ? '' : 'none';
    rejectButton.hidden = !canReject;
    rejectButton.style.display = canReject ? '' : 'none';
    modal.querySelector('[data-reject-form]').action = `/comercial/solicitudes/rechazar/${encodeURIComponent(cite)}/`;
    modal.querySelector('[data-reject-form]').hidden = true;
    modal.hidden = false; document.body.classList.add('modal-open');
  };
  document.querySelectorAll('.request-card-clickable').forEach((card) => {
    card.addEventListener('click', (event) => { if (!event.target.closest('a,button')) open(card); });
    card.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(card); } });
  });
  modal.querySelector('[data-request-close]').addEventListener('click', close);
  modal.addEventListener('click', (event) => { if (event.target === modal) close(); });
  forwardLink.addEventListener('click', (event) => {
    event.preventDefault();
    if (window.confirm('¿Derivar esta solicitud a Planta Técnica?')) {
      postAction(forwardLink.href, { confirm: 'yes' });
    }
  });
  cancelButton.addEventListener('click', () => {
    if (window.confirm('¿Cancelar esta solicitud? Se conservará en el historial.')) {
      postAction(`/comercial/solicitudes/cancelar/${encodeURIComponent(modal.querySelector('[data-modal-cite]').textContent)}/`, { confirm: 'yes' });
    }
  });
  const rejectForm = modal.querySelector('[data-reject-form]');
  rejectButton.addEventListener('click', () => {
    rejectButton.hidden = true;
    openRejectConfirmation(rejectForm, close);
  });
  rejectForm.addEventListener('submit', (event) => event.preventDefault());
  modal.querySelector('[data-reject-cancel]').addEventListener('click', () => { rejectForm.hidden = true; rejectButton.hidden = false; });
}

function initializePlantRequests() {
  const modal = document.querySelector('[data-plant-modal]');
  if (!modal) return;
  const details = modal.querySelector('[data-plant-details]');
  let activeCite = '';
  const value = (card, key) => card.querySelector(`[data-plant-detail="${key}"]`)?.textContent.trim() || '-';
  const getCsrfToken = () => {
    const tokenElement = document.querySelector('[name="csrfmiddlewaretoken"]');
    if (tokenElement && tokenElement.value) return tokenElement.value;

    const cookie = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='));

    if (!cookie) return '';
    return decodeURIComponent(cookie.split('=')[1] || '');
  };
  const close = () => { modal.hidden = true; document.body.classList.remove('modal-open'); };
  const submitDecision = (decision, reason = '') => {
    const form = document.createElement('form');
    form.method = 'post';
    form.action = `/planta-tecnica/encargado/solicitud/decidir/${encodeURIComponent(activeCite)}/`;
    const token = getCsrfToken();
    form.innerHTML = `<input type="hidden" name="decision" value="${decision}"><input type="hidden" name="reason" value="${reason.replace(/"/g, '&quot;')}">`;
    if (token) {
      form.innerHTML += `<input type="hidden" name="csrfmiddlewaretoken" value="${token}">`;
    }
    document.body.appendChild(form);
    form.submit();
  };
  const open = (card) => {
    activeCite = card.dataset.plantCite;
    modal.querySelector('[data-plant-cite]').textContent = activeCite;
    const isMultipoint = value(card, 'type') === 'Instalación Punto Multipunto';
    const requestFields = [
      ['Solicitante', 'applicant'],
      ['', ''],
      ['Tipo de solicitud', 'type'],
      ['Prioridad', 'priority'],
      ...(!isMultipoint ? [['PUNTO ORIGEN', 'origin'], ['UBICACION ORIGEN', 'origin-location']] : []),
      ['PUNTO DESTINO', 'destination'],
      ['UBICACION DESTINO', 'destination-location'],
      ...(!isMultipoint ? [['COORDENADA ORIGEN', 'origin-coordinates']] : []),
      ['COORDENADA DESTINO', 'destination-coordinates'],
      ...(value(card, 'requirements') !== '-' ? [['Requisitos', 'requirements']] : []),
    ];
    details.innerHTML = requestFields.map(([label, key]) => label
      ? `<div><b>${label}</b><span>${value(card, key)}</span></div>`
      : '<div aria-hidden="true" style="visibility:hidden"></div>').join('');
    modal.querySelector('[data-plant-reject-form]').hidden = true;
    modal.querySelector('[data-plant-approve]').hidden = value(card, 'status') !== 'PENDIENTE';
    modal.querySelector('[data-plant-reject]').hidden = value(card, 'status') !== 'PENDIENTE';
    modal.hidden = false;
    document.body.classList.add('modal-open');
  };
  document.querySelectorAll('.plant-request-card').forEach((card) => {
    card.addEventListener('click', (event) => { if (!event.target.closest('a,button')) open(card); });
    card.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(card); } });
  });
  modal.querySelector('[data-plant-close]').addEventListener('click', close);
  modal.addEventListener('click', (event) => { if (event.target === modal) close(); });
  modal.querySelector('[data-plant-approve]').addEventListener('click', () => { if (window.confirm('¿Estás seguro de aprobar esta solicitud?')) submitDecision('APROBADO'); });
  modal.querySelector('[data-plant-reject]').addEventListener('click', () => { modal.querySelector('[data-plant-reject-form]').hidden = false; modal.querySelector('#plant-reject-reason').focus(); });
  modal.querySelector('[data-plant-cancel]').addEventListener('click', () => { modal.querySelector('[data-plant-reject-form]').hidden = true; });
  modal.querySelector('[data-plant-confirm-reject]').addEventListener('click', () => { const reason = modal.querySelector('#plant-reject-reason').value.trim(); if (!reason) return modal.querySelector('#plant-reject-reason').focus(); if (window.confirm('¿Estás seguro de rechazar esta solicitud?')) submitDecision('RECHAZADO', reason); });
}

function initializeSystemsRequests() {
  const modal = document.querySelector('[data-systems-modal]');
  if (!modal) return;
  const details = modal.querySelector('[data-systems-details]');
  const form = modal.querySelector('[data-systems-decision-form]');
  const rejectForm = modal.querySelector('[data-systems-reject-form]');
  const getValue = (card, key) => card.querySelector(`[data-systems-detail="${key}"]`)?.textContent.trim() || '-';
  const close = () => { modal.hidden = true; document.body.classList.remove('modal-open'); };
  const open = (card) => {
    modal.querySelector('[data-systems-modal-cite]').textContent = card.dataset.systemsCite;
    form.action = card.dataset.systemsUrl;
    const isMultipoint = getValue(card, 'type') === 'Instalación Punto Multipunto';
    const fields = [
      ['Solicitante', 'applicant'],
      ['Correo electrónico', 'email'],
      ['Tipo de solicitud', 'type'],
      ['Prioridad', 'priority'],
      ...(!isMultipoint ? [['Punto de origen', 'origin'], ['Ubicación de origen', 'origin-location'], ['Coordenadas de origen', 'origin-coordinates']] : []),
      ['Punto de destino', 'destination'],
      ['Ubicación de destino', 'destination-location'],
      ['Coordenadas de destino', 'destination-coordinates'],
      ['Requisitos', 'requirements'],
    ];
    details.replaceChildren(...fields.map(([label, key]) => {
      const field = document.createElement('div');
      const heading = document.createElement('b');
      const content = document.createElement('span');
      heading.textContent = label;
      content.textContent = getValue(card, key);
      field.append(heading, content);
      return field;
    }));
    rejectForm.hidden = true;
    modal.querySelector('[data-systems-actions]').hidden = false;
    modal.querySelector('#systems-reject-reason').value = '';
    modal.hidden = false;
    document.body.classList.add('modal-open');
  };
  document.querySelectorAll('.systems-request-card').forEach((card) => {
    card.addEventListener('click', (event) => { if (!event.target.closest('a,button')) open(card); });
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        open(card);
      }
    });
  });
  modal.querySelector('[data-systems-close]').addEventListener('click', close);
  modal.addEventListener('click', (event) => { if (event.target === modal) close(); });
  modal.querySelector('[data-systems-reject]').addEventListener('click', () => {
    modal.querySelector('[data-systems-actions]').hidden = true;
    rejectForm.hidden = false;
    modal.querySelector('#systems-reject-reason').focus();
  });
  modal.querySelector('[data-systems-cancel]').addEventListener('click', () => {
    rejectForm.hidden = true;
    modal.querySelector('[data-systems-actions]').hidden = false;
  });
  rejectForm.addEventListener('submit', (event) => {
    if (!modal.querySelector('#systems-reject-reason').value.trim()) {
      event.preventDefault();
      modal.querySelector('#systems-reject-reason').focus();
    }
  });
}

function openRejectConfirmation(rejectForm, closeDetails) {
  const confirmation = document.createElement('div');
  confirmation.className = 'request-confirm-modal';
  confirmation.innerHTML = `<div class="request-confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="reject-confirm-title"><span class="confirm-icon">!</span><h2 id="reject-confirm-title">¿Estás seguro de rechazar esta propuesta?</h2><p>Esta acción quedará registrada en el historial de la solicitud.</p><label for="confirm-reject-reason">Motivo del rechazo</label><textarea id="confirm-reject-reason" rows="4" required placeholder="Escribe el motivo"></textarea><div class="request-confirm-actions"><button type="button" class="button secondary" data-confirm-cancel>Cancelar</button><button type="button" class="button danger-button" data-confirm-accept>Confirmar rechazo</button></div></div>`;
  document.body.appendChild(confirmation);
  const reason = confirmation.querySelector('textarea');
  const close = () => confirmation.remove();
  confirmation.querySelector('[data-confirm-cancel]').addEventListener('click', close);
  confirmation.addEventListener('click', (event) => { if (event.target === confirmation) close(); });
  confirmation.querySelector('[data-confirm-accept]').addEventListener('click', () => {
    if (!reason.value.trim()) { reason.focus(); return; }
    rejectForm.querySelector('textarea[name="reason"]').value = reason.value.trim();
    close();
    closeDetails();
    rejectForm.submit();
  });
  reason.focus();
}

function createLocationPicker(requestForm) {
  if (!window.L) return null;
  const locationNames = ['origin', 'destination', 'installation'];
  const locationLabels = {
    origin: { point: 'PUNTO ORIGEN', location: 'UBICACION ORIGEN', coordinate: 'COORDENADA ORIGEN', placeholder: 'Oficina central, sucursal o referencia' },
    destination: { point: 'PUNTO DESTINO', location: 'UBICACION DESTINO', coordinate: 'COORDENADA DESTINO', placeholder: 'Sucursal, cliente o punto de destino' },
    installation: { point: 'PUNTO DE INSTALACION PRINCIPAL', location: 'UBICACION DEL PUNTO PRINCIPAL', coordinate: 'COORDENADA DEL PUNTO PRINCIPAL', placeholder: 'Referencia del punto principal' },
  };
  const locationState = { target: null, marker: null, selected: {} };
  const modal = document.createElement('div');
  modal.className = 'location-modal';
  modal.hidden = true;
  modal.innerHTML = `<div class="location-dialog" role="dialog" aria-modal="true" aria-labelledby="location-title"><div class="location-dialog-header"><div><span class="eyebrow">Selector de ubicacion</span><h2 id="location-title">Elige un punto en el mapa</h2></div><button type="button" class="location-close" aria-label="Cerrar">&times;</button></div><div class="location-search"><input type="search" placeholder="Buscar calle, zona o lugar en La Paz y El Alto"><button type="button" class="button" data-location-search>Buscar</button></div><p class="location-hint">Haz clic en el mapa para seleccionar la ubicacion exacta.</p><div class="location-map" data-location-map></div><div class="location-result" data-location-result>Selecciona una ubicacion para continuar.</div><div class="location-actions"><button type="button" class="button secondary" data-location-cancel>Cancelar</button><button type="button" class="button" data-location-accept disabled>Aceptar ubicacion</button></div></div>`;
  document.body.appendChild(modal);
  const mapElement = modal.querySelector('[data-location-map]');
  const searchInput = modal.querySelector('input[type="search"]');
  const result = modal.querySelector('[data-location-result]');
  const acceptButton = modal.querySelector('[data-location-accept]');
  const map = L.map(mapElement).setView([-16.53, -68.17], 12);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3nj0_1_480a847a36a7a0a3e0c8b7f9', { attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20 }).addTo(map);

  const close = () => { modal.hidden = true; locationState.target = null; };
  const showSelection = (latitude, longitude, address) => {
    if (locationState.marker) locationState.marker.setLatLng([latitude, longitude]);
    else locationState.marker = L.marker([latitude, longitude]).addTo(map);
    locationState.selected = { latitude, longitude, address: address || `Ubicacion seleccionada (${latitude.toFixed(6)}, ${longitude.toFixed(6)})` };
    result.textContent = `${locationState.selected.address} | ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
    acceptButton.disabled = false;
  };
  const reverseGeocode = async (latitude, longitude) => {
    result.textContent = 'Consultando direccion...';
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`, { headers: { Accept: 'application/json' } });
      const data = await response.json();
      showSelection(latitude, longitude, data.display_name);
    } catch (error) {
      showSelection(latitude, longitude, 'Direccion no disponible');
    }
  };
  const search = async () => {
    const query = searchInput.value.trim();
    if (!query) return;
    result.textContent = 'Buscando ubicacion...';
    try {
      const params = new URLSearchParams({ format: 'jsonv2', q: `${query}, Bolivia`, limit: '1', countrycodes: 'bo', viewbox: '-68.35,-16.35,-67.95,-16.75', bounded: '1' });
      const response = await fetch(`https://nominatim.openstreetmap.org/search?${params}`, { headers: { Accept: 'application/json' } });
      const matches = await response.json();
      if (!matches.length) { result.textContent = 'No encontramos esa ubicacion dentro de La Paz y El Alto.'; return; }
      const match = matches[0];
      const latitude = Number(match.lat);
      const longitude = Number(match.lon);
      map.setView([latitude, longitude], 16);
      showSelection(latitude, longitude, match.display_name);
    } catch (error) {
      result.textContent = 'No se pudo realizar la busqueda. Intenta nuevamente.';
    }
  };
  map.on('click', (event) => reverseGeocode(event.latlng.lat, event.latlng.lng));
  modal.querySelector('[data-location-search]').addEventListener('click', search);
  searchInput.addEventListener('keydown', (event) => { if (event.key === 'Enter') search(); });
  modal.querySelector('.location-close').addEventListener('click', close);
  modal.querySelector('[data-location-cancel]').addEventListener('click', close);
  acceptButton.addEventListener('click', () => {
    const target = locationState.target;
    const nameInput = requestForm.querySelector(`[name="${target}"]`);
    const locationInput = requestForm.querySelector(`[name="${target}_location"]`);
    const coordinateInput = requestForm.querySelector(`[name="${target}_coordinates"]`);
    locationInput.value = locationState.selected.address;
    coordinateInput.value = `${locationState.selected.latitude.toFixed(6)}, ${locationState.selected.longitude.toFixed(6)}`;
    coordinateInput.readOnly = true;
    locationInput.readOnly = true;
    locationInput.closest('.field').classList.add('location-selected');
    coordinateInput.closest('.field').classList.add('location-selected');
    close();
  });
  locationNames.forEach((target) => {
    const nameInput = requestForm.querySelector(`[name="${target}"]`);
    const coordinateInput = requestForm.querySelector(`[name="${target}_coordinates"]`);
    if (!nameInput || !coordinateInput) return;
    const locationField = document.createElement('div');
    locationField.className = 'field location-field';
    const locationLabel = document.createElement('label');
    locationLabel.textContent = locationLabels[target].location;
    const locationInput = document.createElement('input');
    locationInput.name = `${target}_location`;
    locationInput.readOnly = true;
    locationInput.required = true;
    locationInput.placeholder = 'Se completara desde el mapa';
    locationField.append(locationLabel, locationInput);
    coordinateInput.readOnly = true;
    const nameField = nameInput.closest('.field');
    const coordinateField = coordinateInput.closest('.field');
    const formGrid = nameField.parentNode;
    const row = document.createElement('div');
    row.className = 'location-row';
    const detailsRow = document.createElement('div');
    detailsRow.className = 'location-details-row';
    row.dataset.locationGroup = target;
    detailsRow.dataset.locationGroup = target;
    formGrid.insertBefore(row, nameField);
    formGrid.insertBefore(detailsRow, nameField);
    row.appendChild(nameField);
    nameField.querySelector('label').textContent = locationLabels[target].point;
    coordinateField.querySelector('label').textContent = locationLabels[target].coordinate;
    nameInput.placeholder = locationLabels[target].placeholder;
    detailsRow.appendChild(locationField);
    detailsRow.appendChild(coordinateField);
    const actionField = document.createElement('div');
    actionField.className = 'field location-map-action';
    const actionLabel = document.createElement('label');
    actionLabel.textContent = 'MAPA';
    actionField.appendChild(actionLabel);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button secondary map-trigger';
    button.dataset.locationTarget = target;
    button.textContent = '📍';
    button.title = 'Seleccionar ubicación en el mapa';
    button.setAttribute('aria-label', 'Seleccionar ubicación en el mapa');
    actionField.appendChild(button);
    row.appendChild(actionField);
    button.addEventListener('click', () => {
      locationState.target = target;
      locationState.selected = {};
      acceptButton.disabled = true;
      result.textContent = 'Selecciona una ubicacion para continuar.';
      searchInput.value = '';
      modal.hidden = false;
      window.setTimeout(() => { map.invalidateSize(); map.setView([-16.53, -68.17], 12); }, 50);
    });
  });
  return { reset: () => locationNames.forEach((target) => { requestForm.querySelector(`[name="${target}"]`).value = ''; requestForm.querySelector(`[name="${target}_location"]`).value = ''; requestForm.querySelector(`[name="${target}_coordinates"]`).value = ''; requestForm.querySelector(`[data-location-target="${target}"]`).textContent = '📍'; }) };
}
