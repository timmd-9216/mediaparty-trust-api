document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('options-form');
  const input = document.getElementById('apiEndpoint');
  const homepageInput = document.getElementById('homepageArticles');
  const status = document.getElementById('status');

  chrome.storage.sync.get(['apiEndpoint', 'homepageArticles'], (items) => {
    if (items.apiEndpoint) {
      input.value = items.apiEndpoint;
    }

    if (isValidHomepageArticles(items.homepageArticles)) {
      homepageInput.value = Number(items.homepageArticles);
    } else {
      homepageInput.value = 5;
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const endpoint = input.value.trim();
    const homepageCount = parseInt(homepageInput.value, 10);

    if (!endpoint) {
      showStatus('Por favor ingresa una URL válida.', true);
      return;
    }

    if (!isValidHomepageArticles(homepageCount)) {
      showStatus('La cantidad de notas debe ser un número entre 1 y 20.', true);
      return;
    }

    try {
      await chrome.storage.sync.set({
        apiEndpoint: endpoint,
        homepageArticles: homepageCount
      });
      showStatus('Guardado correctamente. Puedes cerrar esta pestaña.', false);
    } catch (error) {
      console.error('Metricas Periodismo: error guardando opciones', error);
      showStatus('No se pudo guardar. Revisa la consola para más detalles.', true);
    }
  });

  function showStatus(message, isError) {
    status.textContent = message;
    status.style.color = isError ? '#d93025' : '#0b8043';
  }

  function isValidHomepageArticles(value) {
    if (value === undefined || value === null) {
      return false;
    }

    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= 1 && parsed <= 20;
  }
});
