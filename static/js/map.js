/**
 * PRANVYRA Leaflet.js Interactive Air Map
 */
window.PranvyraMap = {
  map: null,
  userMarker: null,
  stationLayer: null,

  init(lat = 28.6139, lon = 77.2090, aqi = 168) {
    const mapEl = document.getElementById('airQualityMap');
    if (!mapEl || this.map) return;

    try {
      this.map = L.map('airQualityMap', {
        center: [lat, lon],
        zoom: 12,
        zoomControl: true
      });

      // CartoDB Dark Matter tiles for premium climate tech theme
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(this.map);

      this.updateLocation(lat, lon, aqi);
    } catch (e) {
      console.warn("Leaflet map initialization skipped or failed:", e);
    }
  },

  updateLocation(lat, lon, aqi = 168) {
    if (!this.map) return;

    this.map.setView([lat, lon], 12);

    if (this.userMarker) {
      this.map.removeLayer(this.userMarker);
    }

    if (this.stationLayer) {
      this.map.removeLayer(this.stationLayer);
    }

    // Determine marker color
    let pinColor = '#16A88A';
    if (aqi > 200) pinColor = '#8E24AA';
    else if (aqi > 150) pinColor = '#E46F65';
    else if (aqi > 100) pinColor = '#FF9800';
    else if (aqi > 50) pinColor = '#E7A83E';

    // Custom pulsing SVG icon
    const customIcon = L.divIcon({
      className: 'custom-aqi-pin',
      html: `
        <div style="
          width: 34px;
          height: 34px;
          border-radius: 50%;
          background: ${pinColor};
          border: 3px solid #FFFFFF;
          box-shadow: 0 0 16px ${pinColor};
          display: flex;
          align-items: center;
          justify-content: center;
          color: #FFF;
          font-weight: 800;
          font-size: 11px;
          font-family: sans-serif;
        ">${aqi}</div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 17]
    });

    this.userMarker = L.marker([lat, lon], { icon: customIcon })
      .addTo(this.map)
      .bindPopup(`
        <div style="font-family: sans-serif; padding: 4px;">
          <strong style="color: #123D35;">Active Urban Location</strong><br>
          <span>US EPA AQI: <b style="color: ${pinColor};">${aqi}</b></span><br>
          <small style="color: #666;">Copernicus CAMS Assimilation</small>
        </div>
      `)
      .openPopup();

    // Surrounding ambient atmospheric coverage circles
    this.stationLayer = L.layerGroup();
    
    // Add regional dispersion zones
    const offsets = [
      { dLat: 0.04, dLon: 0.03, diff: -15, label: "North-East Suburb" },
      { dLat: -0.03, dLon: -0.04, diff: +22, label: "Industrial Transit Corridor" },
      { dLat: 0.02, dLon: -0.05, diff: -8, label: "Urban Park & Ridge" },
      { dLat: -0.04, dLon: 0.02, diff: +14, label: "Highway Ring Intersection" }
    ];

    offsets.forEach(off => {
      const sLat = lat + off.dLat;
      const sLon = lon + off.dLon;
      const sAqi = Math.max(20, aqi + off.diff);
      let sColor = '#16A88A';
      if (sAqi > 200) sColor = '#8E24AA';
      else if (sAqi > 150) sColor = '#E46F65';
      else if (sAqi > 100) sColor = '#FF9800';
      else if (sAqi > 50) sColor = '#E7A83E';

      const circle = L.circle([sLat, sLon], {
        color: sColor,
        fillColor: sColor,
        fillOpacity: 0.22,
        radius: 1800
      }).bindPopup(`<strong>${off.label}</strong><br>Estimated AQI: <b>${sAqi}</b>`);
      
      this.stationLayer.addLayer(circle);
    });

    this.stationLayer.addTo(this.map);
  },

  invalidateSize() {
    if (this.map) {
      setTimeout(() => this.map.invalidateSize(), 200);
    }
  }
};

