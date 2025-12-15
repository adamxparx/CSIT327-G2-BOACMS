(function() {
  function todayStr() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  function setDateConstraints() {
    const min = todayStr(); // ✅ min = today
    const dateInputs = document.querySelectorAll(
      'input[type="date"], input[name$="appointment_date"]'
    );
    
    dateInputs.forEach(inp => {
      try { inp.min = min; } catch(e) {}
      inp.addEventListener('change', () => validateDate(inp));
      inp.addEventListener('input', () => inp.setCustomValidity(''));
    });
  }

  function validateDate(input) {
    if (!input.value) return true;
    const min = input.min || todayStr();
    if (input.value < min) {
      input.setCustomValidity('Please select today or a future date.');
      input.reportValidity();
      return false;
    }
    input.setCustomValidity('');
    return true;
  }

  function attachDateGuards() {
    const forms = document.querySelectorAll('.auth-form, .cert');
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        const dateInputs = form.querySelectorAll(
          'input[type="date"], input[name$="appointment_date"]'
        );
        let ok = true;
        dateInputs.forEach(inp => { if (!validateDate(inp)) ok = false; });
        if (!ok) e.preventDefault();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setDateConstraints();
    attachDateGuards();
  });
})();
