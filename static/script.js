// Handle file upload
document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const messageDiv = document.getElementById('uploadMessage');
    const formData = new FormData(form);
  
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        messageDiv.textContent = result.message || result.error;
        messageDiv.style.color = response.ok ? 'green' : 'red';
        console.log('Upload Response:', result); // Debug
    } catch (error) {
        messageDiv.textContent = 'Error uploading file';
        messageDiv.style.color = 'red';
        console.error('Upload error:', error);
    }
  });
  
  // Handle analysis submission
  async function submitData() {
    const product = document.getElementById('product').value;
    const region = document.getElementById('region').value || null;
    const inventoryStatus = document.getElementById('inventoryStatus');
    const currentStock = document.getElementById('currentStock');
    const totalDemand = document.getElementById('totalDemand');
    const aiOutput = document.getElementById('aiOutput');
    const chartCanvas = document.getElementById('forecastChart');
  
    if (!product) {
        inventoryStatus.textContent = 'Please enter a product name';
        inventoryStatus.style.color = 'red';
        return;
    }
  
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product, region })
        });
        const result = await response.json();
  
        console.log('Analyze Response:', result); // Debug the full response
  
        if (response.ok) {
            // Update inventory status
            inventoryStatus.textContent = result.status || 'Unknown';
            inventoryStatus.style.color = 
                result.status === 'Restock Needed' ? 'red' : 
                result.status === 'Overstocked' ? 'orange' : 'green';
            
            // Update stock and demand
            currentStock.textContent = result.current_stock !== undefined ? result.current_stock : 'N/A';
            totalDemand.textContent = result.total_demand !== undefined ? result.total_demand : 'N/A';
  
            // Update AI recommendation
            aiOutput.textContent = result.ai || 'No recommendation available';
            aiOutput.style.color = 'black';
  
            // Update chart
            const ctx = chartCanvas.getContext('2d');
            // Reset canvas dimensions to match fixed card height
            chartCanvas.height = 180; // Adjusted to fit within 250px card (allowing for padding and title)
            if (window.forecastChart && typeof window.forecastChart.destroy === 'function') {
                window.forecastChart.destroy(); // Destroy previous chart
            }
            if (result.labels && result.values && Array.isArray(result.labels) && Array.isArray(result.values) && result.labels.length === result.values.length) {
                window.forecastChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result.labels,
                        datasets: [{
                            label: 'Predicted Units Sold',
                            data: result.values,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: { beginAtZero: true, title: { display: true, text: 'Units' } },
                            x: { title: { display: true, text: 'Date' } }
                        },
                        responsive: false, // Disable responsiveness to lock height
                        maintainAspectRatio: false,
                        height: 180 // Match canvas height
                    }
                });
                console.log('Chart created successfully');
            } else {
                console.error('Invalid chart data:', result.labels, result.values);
                inventoryStatus.textContent = 'Error: Invalid or missing forecast data';
                inventoryStatus.style.color = 'red';
            }
        } else {
            inventoryStatus.textContent = result.error || 'Analysis failed';
            inventoryStatus.style.color = 'red';
            currentStock.textContent = '';
            totalDemand.textContent = '';
            aiOutput.textContent = 'No suggestions available';
        }
    } catch (error) {
        console.error('Fetch error:', error);
        inventoryStatus.textContent = `Error during analysis: ${error.message || error}`;
        inventoryStatus.style.color = 'red';
        currentStock.textContent = '';
        totalDemand.textContent = '';
        aiOutput.textContent = 'No suggestions available';
        // Only destroy if chart exists and is a function
        if (window.forecastChart && typeof window.forecastChart.destroy === 'function') {
            window.forecastChart.destroy();
        }
    }
  }