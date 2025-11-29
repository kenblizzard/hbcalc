<template>
  <div id="app">
    <div class="container">
      <header>
        <h1>Voltex Highbay Lighting Calculator</h1>
        <p>Calculate optimal lighting layouts for your space</p>
      </header>

      <div class="main-content">
        <!-- Input Form -->
        <section class="input-section">
          <h2>Room Dimensions</h2>
          <form @submit.prevent="calculate" class="input-form">
            <div class="form-group">
              <label for="roomLength">Room Length (meters)</label>
              <input
                id="roomLength"
                v-model.number="inputs.roomLength"
                type="number"
                step="0.1"
                min="0.1"
                required
                placeholder="e.g., 20"
              />
            </div>

            <div class="form-group">
              <label for="roomWidth">Room Width (meters)</label>
              <input
                id="roomWidth"
                v-model.number="inputs.roomWidth"
                type="number"
                step="0.1"
                min="0.1"
                required
                placeholder="e.g., 15"
              />
            </div>

            <div class="form-group">
              <label for="roomHeight">Room Height (meters)</label>
              <input
                id="roomHeight"
                v-model.number="inputs.roomHeight"
                type="number"
                step="0.1"
                min="0.1"
                required
                placeholder="e.g., 7.5"
              />
            </div>

            <div class="form-group" style="display: none;">
              <label for="requiredIlluminance">Required Illuminance (lux)</label>
              <input
                id="requiredIlluminance"
                v-model.number="inputs.requiredIlluminance"
                type="number"
                step="1"
                min="0"
                placeholder="Default: 3"
              />
            </div>

            <div class="form-group" style="display: none;">
              <label for="workingPlaneHeight">Working Plane Height (meters)</label>
              <input
                id="workingPlaneHeight"
                v-model.number="inputs.workingPlaneHeight"
                type="number"
                step="0.1"
                min="0.1"
                placeholder="Default: 3"
              />
            </div>

            <button type="submit" class="calculate-btn">Calculate</button>
          </form>
        </section>

        <!-- Recommended Highbay -->
        <section v-if="recommendedHighbay" class="recommended-section">
          <h2>Recommended fixture</h2>
          <div class="highbay-card">
            <h3>{{ recommendedHighbay.productName }}</h3>
            <div class="highbay-details">
              <p><strong>Product Code:</strong> {{ recommendedHighbay.productCode }}</p>
              <p><strong>Wattage:</strong> {{ recommendedHighbay.wattage }}W</p>
              <p><strong>Recommended Height Range:</strong> 
                {{ recommendedHighbay.recommendedMinimumRoomHeightInMeters }}m - 
                {{ recommendedHighbay.recommendedMaximumRoomHeightInMeters }}m
              </p>
            </div>
          </div>
        </section>

        <!-- Results Section -->
        <section v-if="results" class="results-section">
          <h2>Calculation Results</h2>
          
          <div v-if="!results.success" class="error-message">
            <p><strong>Error:</strong> {{ results.error }}</p>
          </div>

          <div v-else>
            <!-- Key Metrics -->
            <div class="metrics-grid">
              <div class="metric-card primary">
                <h3>Number of Fixtures</h3>
                <p class="metric-value">{{ results.calculations.numFixtures }}</p>
                <p class="metric-label">Required fixtures for optimal lighting</p>
              </div>
              <div class="metric-card">
                <h3>Room Cavity Index (K)</h3>
                <p class="metric-value">{{ results.calculations.K.toFixed(2) }}</p>
                <p class="metric-label">Room proportion measure</p>
              </div>
              <div class="metric-card">
                <h3>Utilization Factor (Uf)</h3>
                <p class="metric-value">{{ results.calculations.Uf.toFixed(2) }}</p>
                <p class="metric-label">Light utilization efficiency</p>
              </div>
              <div class="metric-card">
                <h3>Mounting Height</h3>
                <p class="metric-value">{{ results.calculations.mountingHeight.toFixed(2) }}m</p>
                <p class="metric-label">Fixture mounting height</p>
              </div>
              <div class="metric-card">
                <h3>Aspect Ratio</h3>
                <p class="metric-value">{{ results.calculations.aspectRatio.toFixed(2) }}</p>
                <p class="metric-label">Length to width ratio</p>
              </div>
            </div>

            <!-- Detailed Results Table -->
            <div class="results-table-container">
              <h3>Detailed Results</h3>
              <table class="results-table">
                <thead>
                  <tr>
                    <th>Parameter</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(result, index) in results.results" :key="index">
                    <td>{{ result[0] }}</td>
                    <td>{{ result[1] }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Array Layouts -->
            <div class="array-layouts">
              <div v-if="results.arrays.even" class="array-card">
                <h3>Even Array Layout</h3>
                <!-- Visual Layout Display -->
                <div class="layout-visualization">
                  <div 
                    class="layout-grid" 
                    :style="getLayoutGridStyle(results.arrays.even.array)"
                  >
                    <div 
                      v-for="i in results.arrays.even.fixtures" 
                      :key="i" 
                      class="light-bulb-icon"
                    ></div>
                  </div>
                </div>
                <div class="array-details">
                  <div class="array-grid">
                    <div class="array-item">
                      <strong>Layout:</strong> {{ results.arrays.even.array[0] }} × {{ results.arrays.even.array[1] }}
                    </div>
                    <div class="array-item">
                      <strong>Total Fixtures:</strong> {{ results.arrays.even.fixtures }}
                    </div>
                    <div class="array-item">
                      <strong>Spacing (Length):</strong> {{ results.arrays.even.spacingLength.toFixed(2) }}m
                    </div>
                    <div class="array-item">
                      <strong>Spacing (Width):</strong> {{ results.arrays.even.spacingWidth.toFixed(2) }}m
                    </div>
                    <div class="array-item">
                      <strong>SHR (Length):</strong> {{ results.arrays.even.shrLength.toFixed(2) }}
                    </div>
                    <div class="array-item">
                      <strong>SHR (Width):</strong> {{ results.arrays.even.shrWidth.toFixed(2) }}
                    </div>
                  </div>
                  <p class="array-info">{{ formatArrayInfo(results.arrays.even, results.calculations.numFixtures, getRequiredIlluminance()) }}</p>
                </div>
              </div>
              <div v-if="results.arrays.odd" class="array-card">
                <h3>Odd Array Layout</h3>
                <!-- Visual Layout Display -->
                <div class="layout-visualization">
                  <div 
                    class="layout-grid" 
                    :style="getLayoutGridStyle(results.arrays.odd.array)"
                  >
                    <div 
                      v-for="i in results.arrays.odd.fixtures" 
                      :key="i" 
                      class="light-bulb-icon"
                    ></div>
                  </div>
                </div>
                <div class="array-details">
                  <div class="array-grid">
                    <div class="array-item">
                      <strong>Layout:</strong> {{ results.arrays.odd.array[0] }} × {{ results.arrays.odd.array[1] }}
                    </div>
                    <div class="array-item">
                      <strong>Total Fixtures:</strong> {{ results.arrays.odd.fixtures }}
                    </div>
                    <div class="array-item">
                      <strong>Spacing (Length):</strong> {{ results.arrays.odd.spacingLength.toFixed(2) }}m
                    </div>
                    <div class="array-item">
                      <strong>Spacing (Width):</strong> {{ results.arrays.odd.spacingWidth.toFixed(2) }}m
                    </div>
                    <div class="array-item">
                      <strong>SHR (Length):</strong> {{ results.arrays.odd.shrLength.toFixed(2) }}
                    </div>
                    <div class="array-item">
                      <strong>SHR (Width):</strong> {{ results.arrays.odd.shrWidth.toFixed(2) }}
                    </div>
                  </div>
                  <p class="array-info">{{ formatArrayInfo(results.arrays.odd, results.calculations.numFixtures, getRequiredIlluminance()) }}</p>
                </div>
              </div>
              <div v-if="!results.arrays.even && !results.arrays.odd" class="array-card">
                <p class="no-array-message">No valid array layouts found. Please adjust your room dimensions or parameters.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { calculateAndDisplay } from './calculateAndDisplay.js';
import { getRecommendedHighbay } from './highbays.js';
import { getFixtureDataByProductCode } from './sampleData.js';

// Reactive state
const inputs = ref({
  roomLength: null,
  roomWidth: null,
  roomHeight: null,
  requiredIlluminance: 3,
  workingPlaneHeight: 3,
  suspensionDistance: 0,
  ceilingReflectance: 0,
  wallsReflectance: 0,
  floorReflectance: 0,
  maintenanceFactor: 0.8
});

const results = ref(null);
const recommendedHighbay = ref(null);

// Watch room height for recommended highbay
watch(() => inputs.value.roomHeight, (newHeight) => {
  if (newHeight && newHeight > 0) {
    try {
      recommendedHighbay.value = getRecommendedHighbay(newHeight);
    } catch (error) {
      recommendedHighbay.value = null;
    }
  } else {
    recommendedHighbay.value = null;
  }
}, { immediate: true });

// Calculate function
function calculate() {
  if (!inputs.value.roomLength || !inputs.value.roomWidth || !inputs.value.roomHeight) {
    alert('Please fill in all required room dimensions');
    return;
  }

  // Get recommended highbay data
  const highbay = recommendedHighbay.value;
  if (!highbay) {
    alert('Please enter a valid room height to get recommendations');
    return;
  }

  // Get fixture data based on recommended highbay product code
  const fixtureData = getFixtureDataByProductCode(highbay.productCode);
  if (!fixtureData) {
    alert(`Fixture data not found for product code: ${highbay.productCode}`);
    return;
  }

  // Prepare calculation inputs using the recommended highbay's fixture data
  const calculationInputs = {
    roomLength: inputs.value.roomLength,
    roomWidth: inputs.value.roomWidth,
    roomHeight: inputs.value.roomHeight,
    workingPlaneHeight: inputs.value.workingPlaneHeight,
    suspensionDistance: inputs.value.suspensionDistance,
    ceilingReflectance: inputs.value.ceilingReflectance,
    wallsReflectance: inputs.value.wallsReflectance,
    floorReflectance: inputs.value.floorReflectance,
    requiredIlluminance: inputs.value.requiredIlluminance,
    maintenanceFactor: inputs.value.maintenanceFactor,
    // Use fixture data from recommended highbay
    luminousFlux: fixtureData.luminousFlux,
    wattage: fixtureData.wattage,
    shrNom: fixtureData.shrNom,
    shrNomModified: fixtureData.shrNom * 1.5, // Apply SHR_FACTOR
    fixtureName: fixtureData.fixtureName,
    ufTable: fixtureData.ufTable
  };

  // Perform calculation
  results.value = calculateAndDisplay(calculationInputs);
}

// Get required illuminance from results
function getRequiredIlluminance() {
  if (!results.value || !results.value.success) return 3;
  const luxResult = results.value.results.find(r => r[0] === 'Required Lux Level');
  if (luxResult) {
    return parseFloat(luxResult[1].replace(' lux', ''));
  }
  return inputs.value.requiredIlluminance || 3;
}

// Get grid style for layout visualization
function getLayoutGridStyle(array) {
  // array[0] is along length (columns), array[1] is across width (rows)
  return {
    gridTemplateColumns: `repeat(${array[0]}, 1fr)`,
    gridTemplateRows: `repeat(${array[1]}, 1fr)`
  };
}

// Format array information for display
function formatArrayInfo(arrayData, numFixtures, requiredIlluminance) {
  if (!arrayData) return 'No valid array found';
  
  const array = arrayData.array;
  const spacingLength = arrayData.spacingLength.toFixed(2);
  const spacingWidth = arrayData.spacingWidth.toFixed(2);
  const shrLength = arrayData.shrLength.toFixed(2);
  const shrWidth = arrayData.shrWidth.toFixed(2);
  const fixtures = arrayData.fixtures;
  const adjustedE = (requiredIlluminance * (fixtures / numFixtures)).toFixed(0);
  
  return `${array[0]} along length, ${array[1]} across width | ` +
         `Spacing: ${spacingLength}m (L), ${spacingWidth}m (W) | ` +
         `SHR: ${shrLength} (L), ${shrWidth} (W) | ` +
         `Fixtures: ${fixtures}, Lux: ${adjustedE}`;
}
</script>

<style scoped>
* {
  box-sizing: border-box;
}

#app {
  min-height: 100vh;
  background: white;
  padding: 20px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

header {
  text-align: center;
  color: #0065a3;
  margin-bottom: 30px;
}

header h1 {
  font-size: 2.5em;
  margin-bottom: 10px;
  color: #0065a3;
}

header p {
  font-size: 1.2em;
  color: #555;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 30px;
}

@media (min-width: 768px) {
  .main-content {
    grid-template-columns: 1fr 1fr;
  }
  
  .results-section {
    grid-column: 1 / -1;
  }
}

section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

section h2 {
  margin-top: 0;
  color: #333;
  border-bottom: 2px solid #0065a3;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.input-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #555;
}

.form-group input {
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #0065a3;
}

.calculate-btn {
  padding: 15px 30px;
  background: #0065a3;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
  margin-top: 10px;
}

.calculate-btn:hover {
  transform: translateY(-2px);
  background: #005085;
  box-shadow: 0 2px 6px rgba(0, 101, 163, 0.3);
}

.calculate-btn:active {
  transform: translateY(0);
}

.highbay-card {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}

.highbay-card h3 {
  margin-top: 0;
  color: #333;
}

.highbay-details p {
  margin: 8px 0;
  color: #555;
}

.error-message {
  background: #fee;
  border: 2px solid #fcc;
  border-radius: 6px;
  padding: 15px;
  color: #c33;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: #0065a3;
  color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.metric-card h3 {
  margin-top: 0;
  font-size: 0.9em;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.metric-value {
  font-size: 2em;
  font-weight: bold;
  margin: 10px 0 0 0;
}

.results-table-container {
  margin-bottom: 30px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

.results-table th,
.results-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.results-table th {
  background: #f5f7fa;
  font-weight: 600;
  color: #333;
}

.results-table tr:hover {
  background: #f9f9f9;
}

.array-layouts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.array-card {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}

.array-card h3 {
  margin-top: 0;
  color: #333;
}

.layout-visualization {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 30px;
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.layout-grid {
  display: grid;
  gap: 20px;
  width: 100%;
  max-width: 400px;
  aspect-ratio: 1;
  place-items: center;
}

.layout-grid > div {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.light-bulb-icon {
  width: 20px;
  height: 20px;
  max-width: 20px;
  max-height: 20px;
  border-radius: 50%;
  background-color: #0065a3;
  flex-shrink: 0;
}

.array-info {
  color: #555;
  line-height: 1.6;
  margin: 15px 0 0 0;
  padding-top: 15px;
  border-top: 1px solid #ddd;
  font-size: 0.9em;
}

.array-details {
  margin-top: 10px;
}

.array-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 10px;
}

.array-item {
  padding: 8px;
  background: white;
  border-radius: 4px;
  font-size: 0.9em;
}

.array-item strong {
  color: #0065a3;
  display: block;
  margin-bottom: 4px;
}

.no-array-message {
  color: #c33;
  font-style: italic;
  text-align: center;
  padding: 20px;
}

.metric-label {
  font-size: 0.85em;
  opacity: 0.8;
  margin-top: 8px;
  margin-bottom: 0;
}

.metric-card.primary {
  background: #0065a3;
}
</style>
