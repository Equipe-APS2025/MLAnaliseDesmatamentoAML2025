document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('grafico').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: graficoAnos,
            datasets: [{
                label: 'Área Desmatada (km²)',
                data: graficoValores,
                backgroundColor: 'rgba(34, 139, 34, 0.6)',
                borderColor: 'rgba(34, 139, 34, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: 'Ano' } },
                y: { beginAtZero: true, title: { display: true, text: 'Área Desmatada (km²)' } }
            },
            plugins: {
                legend: { display: false },
                tooltip: { mode: 'index', intersect: false }
            }
        }
    });
});
