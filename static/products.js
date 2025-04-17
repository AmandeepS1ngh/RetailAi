let csvData = [];

document.getElementById('csvFileInput').addEventListener('change', function (e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (event) {
    const text = event.target.result;
    csvData = text.trim().split('\n').map(row => row.split(','));
    document.getElementById('viewBtn').disabled = false; // Enable button
  };
  reader.readAsText(file);
});

document.getElementById('viewBtn').addEventListener('click', function () {
  if (csvData.length === 0) return;
  renderTable(csvData);
});

function renderTable(data) {
  const container = document.getElementById('tableContainer');
  const table = document.createElement('table');
  table.className = 'csv-table';

  data.forEach((row, index) => {
    const tr = document.createElement('tr');
    row.forEach(cell => {
      const cellElement = document.createElement(index === 0 ? 'th' : 'td');
      cellElement.textContent = cell;
      tr.appendChild(cellElement);
    });
    table.appendChild(tr);
  });

  container.innerHTML = '';
  container.appendChild(table);
}
