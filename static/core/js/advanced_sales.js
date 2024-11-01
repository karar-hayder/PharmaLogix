document.addEventListener("DOMContentLoaded", function() {
    // Total Sales Over Time Chart
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    const salesDates = JSON.parse(document.getElementById('salesChart').getAttribute('data-sales-dates'));
    const salesAmount = JSON.parse(document.getElementById('salesChart').getAttribute('data-sales-amount'));

    const salesChart = new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: salesDates,
            datasets: [{
                label: 'Total Sales Amount (IQD)',
                data: salesAmount,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                fill: false,
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Sales Amount (IQD)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });

    // Best Selling Products Chart
    const bestSellingCtx = document.getElementById('bestSellingProductsChart').getContext('2d');
    const productNames = JSON.parse(document.getElementById('bestSellingProductsChart').getAttribute('data-product-names'));
    const productRevenues = JSON.parse(document.getElementById('bestSellingProductsChart').getAttribute('data-revenues'));

    const bestSellingProductsChart = new Chart(bestSellingCtx, {
        type: 'bar',
        data: {
            labels: productNames,
            datasets: [{
                label: 'Revenue (IQD)',
                data: productRevenues,
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Revenue (IQD)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Products'
                    }
                }
            }
        }
    });
});
