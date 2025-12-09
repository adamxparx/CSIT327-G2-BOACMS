(function() {
    const MIN = "09:00";
    const MAX = "17:00";

    function setConstraints() {
      // Updated selector to target select elements for time instead of input[type="time"]
      const timeInputs = document.querySelectorAll('select[name$="preferred_time"]');
      timeInputs.forEach(inp => {
        // For select elements, we don't need min/max constraints
        // The options are already limited to valid times
        inp.addEventListener('change', () => validateTime(inp));
      });
    }

    function parseTime(val) {
      if (!val) return null;
      const parts = val.split(":").map(Number);
      if (parts.length < 2) return null;
      return parts[0] * 60 + parts[1];
    }

    function validateTime(input) {
      // For select elements, validation is simpler since only valid options are available
      const value = input.value;
      if (!value) return true;
      
      const v = parseTime(value);
      const min = parseTime(MIN);
      const max = parseTime(MAX);
      
      if (v == null) return true;
      if (v < min || v > max) {
        input.setCustomValidity(`Please select a time between ${MIN} and ${MAX}.`);
        input.reportValidity();
        return false;
      } else {
        input.setCustomValidity('');
        return true;
      }
    }

    function attachFormGuards() {
      const forms = document.querySelectorAll('.auth-form, .cert');
      forms.forEach(form => {
        form.addEventListener('submit', (e) => {
          // Updated selector to target select elements for time
          const timeInputs = form.querySelectorAll('select[name$="preferred_time"]');
          let ok = true;
          timeInputs.forEach(inp => { if (!validateTime(inp)) ok = false; });
          if (!ok) {
            e.preventDefault();
          }
        });
      });
    }

    document.addEventListener('DOMContentLoaded', () => {
      setConstraints();
      attachFormGuards();
    });
  })();