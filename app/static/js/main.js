/* Main interaction script for the shared household ledger. */
(function () {
  const root = document.documentElement;
  const themeForm = document.querySelector('.theme-form');
  const settingsToggle = document.querySelector('.settings-toggle');
  const settingsContent = document.querySelector('.settings-content');
  const modal = document.querySelector('#entry-modal');
  const modalClose = modal ? modal.querySelector('.modal-close') : null;
  const entryTypeInput = modal ? modal.querySelector('input[name="entry_type"]') : null;
  const actionButtons = document.querySelectorAll('[data-modal-target]');
  const filterButtons = document.querySelectorAll('.filter-button');

  const savedTheme = localStorage.getItem('ledger-theme');
  if (savedTheme) {
    root.setAttribute('data-theme', savedTheme);
    if (themeForm) {
      themeForm.theme.value = savedTheme;
    }
  }

  const savedFontSize = localStorage.getItem('ledger-font-size');
  if (savedFontSize) {
    document.body.style.fontSize = `${savedFontSize}px`;
    if (themeForm) {
      themeForm.fontSize.value = savedFontSize;
    }
  }

  if (themeForm) {
    themeForm.addEventListener('change', (event) => {
      if (event.target.name === 'theme') {
        root.setAttribute('data-theme', event.target.value);
        localStorage.setItem('ledger-theme', event.target.value);
      }
      if (event.target.name === 'fontSize') {
        document.body.style.fontSize = `${event.target.value}px`;
        localStorage.setItem('ledger-font-size', event.target.value);
      }
    });
  }

  if (settingsToggle && settingsContent) {
    settingsToggle.addEventListener('click', () => {
      const expanded = settingsToggle.getAttribute('aria-expanded') === 'true';
      settingsToggle.setAttribute('aria-expanded', String(!expanded));
      settingsContent.hidden = expanded;
      if (!expanded) {
        settingsContent.focus?.();
      }
    });
  }

  if (modal && modalClose) {
    const openModal = (entryType) => {
      modal.hidden = false;
      document.body.style.overflow = 'hidden';
      if (entryTypeInput) {
        entryTypeInput.value = entryType;
      }
    };

    const closeModal = () => {
      modal.hidden = true;
      document.body.style.overflow = '';
    };

    actionButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const entryType = button.dataset.entryType || 'expense';
        openModal(entryType);
      });
    });

    modalClose.addEventListener('click', closeModal);
    modal.addEventListener('click', (event) => {
      if (event.target === modal) {
        closeModal();
      }
    });
  }

  // Member ledger filter for quick access from the side index.
  const tableFilterState = {};
  if (filterButtons.length) {
    filterButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const memberId = button.dataset.memberId;
        const target = button.dataset.target;
        if (!target) return;
        const tbody = document.querySelector(`${target} .ledger-table tbody`);
        if (!tbody) return;

        const key = target;
        const isActive = tableFilterState[key] === memberId;
        tableFilterState[key] = isActive ? null : memberId;

        tbody.querySelectorAll('tr').forEach((row) => {
          const rowMember = row.dataset.member;
          if (!tableFilterState[key]) {
            row.hidden = false;
            return;
          }
          if (!rowMember) {
            row.hidden = true;
            return;
          }
          row.hidden = rowMember !== tableFilterState[key];
        });

        const section = document.querySelector(target);
        if (section) {
          section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  const dayButtons = document.querySelectorAll('.day-index');
  let highlightedCell = null;
  dayButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const day = button.dataset.day;
      if (!day) return;
      const cell = document.querySelector(`.calendar-cell[data-date$='-${day}']`);
      if (!cell) return;
      if (highlightedCell) {
        highlightedCell.classList.remove('is-highlighted');
      }
      cell.classList.add('is-highlighted');
      highlightedCell = cell;
      cell.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  });

  // Fetch holidays to display tooltip like interactions.
  fetch('/api/holidays')
    .then((response) => response.json())
    .then((holidays) => {
      holidays.forEach((holiday) => {
        const cell = document.querySelector(
          `.calendar-cell[data-date="${holiday.date}"]`
        );
        if (cell) {
          cell.setAttribute('title', `${holiday.name} (${holiday.source})`);
        }
      });
    })
    .catch(() => {
      /* Silent failure keeps the UI responsive when offline. */
    });
})();
