/**
 * PRANVYRA Chart.js Visualizations
 */
window.PranvyraCharts = {
  trendChart: null,
  commuteChart: null,
  impactChart: null,

  initHourlyTrendChart(trendData, activeMetric = 'aqi') {
    const ctx = document.getElementById('hourlyTrendChart');
    if (!ctx) return;

    if (this.trendChart) {
      this.trendChart.destroy();
    }

    const labels = trendData.labels || [];
    let datasetLabel = 'US EPA AQI';
    let dataValues = trendData.aqi || [];
    let strokeColor = '#E46F65';
    let fillColor = 'rgba(228, 111, 101, 0.15)';

    if (activeMetric === 'pm25') {
      datasetLabel = 'PM2.5 (µg/m³)';
      dataValues = trendData.pm25 || [];
      strokeColor = '#FF9800';
      fillColor = 'rgba(255, 152, 0, 0.15)';
    } else if (activeMetric === 'pm10') {
      datasetLabel = 'PM10 (µg/m³)';
      dataValues = trendData.pm10 || [];
      strokeColor = '#E7A83E';
      fillColor = 'rgba(231, 168, 62, 0.15)';
    }

    this.trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: datasetLabel,
          data: dataValues,
          borderColor: strokeColor,
          backgroundColor: fillColor,
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 2.5,
          pointHoverRadius: 6,
          pointBackgroundColor: strokeColor
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: '#12231E',
            titleColor: '#F7F8F3',
            bodyColor: '#B9E8D7',
            borderColor: 'rgba(22, 168, 138, 0.3)',
            borderWidth: 1,
            padding: 10,
            displayColors: false
          }
        },
        scales: {
          x: {
            grid: {
              color: 'rgba(185, 232, 215, 0.05)'
            },
            ticks: {
              color: '#648278',
              font: { size: 10 },
              maxTicksLimit: 8
            }
          },
          y: {
            grid: {
              color: 'rgba(185, 232, 215, 0.08)'
            },
            ticks: {
              color: '#9EBAAF',
              font: { size: 11 }
            }
          }
        }
      }
    });
  },

  initCommuteCompareChart(compareResult) {
    const ctx = document.getElementById('commuteCompareChart');
    if (!ctx) return;

    if (this.commuteChart) {
      this.commuteChart.destroy();
    }

    const items = compareResult.comparison || [];
    const labels = items.map(i => i.mode_name);
    const emissions = items.map(i => i.emissions_kg);
    const backgroundColors = items.map(i => {
      if (i.is_current) return '#E46F65'; // Coral for user's current vehicle
      if (i.emissions_kg === 0) return '#16A88A'; // Emerald for zero emission
      if (i.emissions_kg < 0.8) return '#22C5A0'; // Light emerald
      if (i.emissions_kg < 1.6) return '#E7A83E'; // Amber
      return '#8E24AA'; // Purple for high
    });

    this.commuteChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Estimated Tailpipe CO₂ (kg)',
          data: emissions,
          backgroundColor: backgroundColors,
          borderRadius: 8,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#12231E',
            titleColor: '#F7F8F3',
            bodyColor: '#B9E8D7',
            borderColor: 'rgba(22, 168, 138, 0.3)',
            borderWidth: 1,
            callbacks: {
              label: (ctx) => ` Tailpipe CO₂: ${ctx.raw} kg`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: '#9EBAAF',
              font: { size: 11 }
            }
          },
          y: {
            grid: { color: 'rgba(185, 232, 215, 0.08)' },
            ticks: {
              color: '#9EBAAF',
              font: { size: 11 },
              callback: (val) => `${val} kg`
            }
          }
        }
      }
    });
  },

  initWeeklyImpactChart(weeklyData) {
    const ctx = document.getElementById('weeklyImpactChart');
    if (!ctx) return;

    if (this.impactChart) {
      this.impactChart.destroy();
    }

    this.impactChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: weeklyData.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
          {
            label: 'Cumulative CO₂ Avoided (kg)',
            data: weeklyData.co2_saved_kg || [1.8, 3.4, 6.1, 9.2, 12.8, 15.6, 18.4],
            borderColor: '#16A88A',
            backgroundColor: 'rgba(22, 168, 138, 0.15)',
            fill: true,
            tension: 0.3,
            borderWidth: 2.5
          },
          {
            label: 'Clean Energy Saved (kWh)',
            data: weeklyData.energy_saved_kwh || [1.2, 3.0, 5.5, 7.8, 10.4, 12.6, 14.8],
            borderColor: '#E7A83E',
            backgroundColor: 'rgba(231, 168, 62, 0.1)',
            fill: true,
            tension: 0.3,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#9EBAAF',
              font: { size: 11 }
            }
          },
          tooltip: {
            backgroundColor: '#12231E',
            titleColor: '#F7F8F3',
            bodyColor: '#B9E8D7',
            borderColor: 'rgba(22, 168, 138, 0.3)',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(185, 232, 215, 0.05)' },
            ticks: { color: '#9EBAAF' }
          },
          y: {
            grid: { color: 'rgba(185, 232, 215, 0.08)' },
            ticks: { color: '#9EBAAF' }
          }
        }
      }
    });
  }
};

