/**
 * VOLTEX HIGHBAY LIGHTING CALCULATOR - JavaScript Implementation
 * 
 * This module provides functions for calculating lighting layouts using Voltex High Bays.
 * It helps determine optimal fixture placement while considering:
 * - Room dimensions and reflectances
 * - Technical specifications of individual fixtures (light output, light distribution, etc)
 * - Lighting requirements (Illuminance levels in Lux)
 * - Spacing constraints (minimum and maximum distances)
 * 
 * It uses the industry standard method for estimating the quantity of fixtures required 
 * to light up a space to a required light level with a specific fixture. 
 * The industry standard method used is called 'the lumen method'.
 */

// ==============================================
// GLOBAL CONSTANTS
// ==============================================

// Multiplier for SHRNOM (Spacing-to-Height Ratio Nominal) from CSV
// This increases the manufacturer's recommended spacing for better uniformity
// This factor allows me to increase SHRNOM until it balanced with results from Relux
const SHR_FACTOR = 1.50;

// Minimum allowed distance between fixtures in meters
// Prevents fixtures from being placed too close together
// 3m seems reasonable but this allows me to change in the backend if required
const MIN_SPACING = 3.0;

// ==============================================
// HELPER FUNCTIONS
// ==============================================

/**
 * Validate that input values are numbers within specified ranges.
 * 
 * @param {string|number} value - Input value to validate
 * @param {string} fieldName - Name of field for error messages
 * @param {number} [minValue] - Minimum allowed value (optional)
 * @param {number} [maxValue] - Maximum allowed value (optional)
 * @returns {number} Validated numeric value
 * @throws {Error} For invalid inputs
 */
function validateInput(value, fieldName, minValue = null, maxValue = null) {
    try {
        const numValue = parseFloat(value);
        
        if (isNaN(numValue)) {
            throw new Error(`Invalid input for ${fieldName}. Please enter a numeric value.`);
        }
        
        // Check minimum value constraint
        if (minValue !== null && numValue < minValue) {
            throw new Error(
                `${fieldName} must be greater than or equal to ${minValue}.`
            );
        }
        
        // Check maximum value constraint
        if (maxValue !== null && numValue > maxValue) {
            throw new Error(
                `${fieldName} must be less than or equal to ${maxValue}.`
            );
        }
        
        return numValue;
    } catch (error) {
        if (error instanceof Error) {
            throw error;
        }
        throw new Error(
            `Invalid input for ${fieldName}. Please enter a numeric value.`
        );
    }
}

/**
 * Calculate the Room Cavity Index (K) - a measure of room proportions.
 * Note: Don't get confused between the Room Cavity Index (RCI) and Room Cavity Ratio (RCR)
 * The calculation used requires the RCI
 * 
 * @param {number} roomLength - Room length in meters
 * @param {number} roomWidth - Room width in meters
 * @param {number} roomHeight - Room height in meters
 * @param {number} workingPlaneHeight - Height of work surface in meters
 * @param {number} suspensionDistance - Fixture suspension distance in meters
 * @returns {number} Room Cavity Index (K) value
 * @throws {Error} For invalid input combinations
 */
function calculateRoomCavityIndex(roomLength, roomWidth, roomHeight, 
                                  workingPlaneHeight, suspensionDistance) {
    // Calculate mounting height (work plane to fixtures)
    const h = (roomHeight - workingPlaneHeight) - suspensionDistance;
    
    // Validate mounting height is positive
    if (h <= 0) {
        throw new Error(
            "Invalid inputs: Working plane height must be greater than suspension distance."
        );
    }
    
    // Standard formula for Room Cavity Index
    return (roomLength * roomWidth) / (h * (roomLength + roomWidth));
}

/**
 * Calculate how many fixtures are needed to achieve desired illuminance.
 * Industry standard method for estimating number of fixtures required in a rectangular room
 * 
 * @param {number} E - Required illuminance in lux (Application dependent)
 * @param {number} roomLength - Room length in meters
 * @param {number} roomWidth - Room width in meters
 * @param {number} luminousFlux - Fixture light output in lumens
 * @param {number} Uf - Utilization factor (0-1)
 * @param {number} [MF=0.8] - Maintenance factor (0-1, default 0.8)
 * @returns {number} Number of fixtures needed (rounded up)
 * @throws {Error} For invalid inputs
 */
function calculateNumberOfFixtures(E, roomLength, roomWidth, luminousFlux, Uf, MF = 0.8) {
    try {
        const flux = parseFloat(luminousFlux);
        
        // Validate all inputs are positive numbers
        if (flux <= 0 || Uf <= 0 || MF <= 0) {
            throw new Error(
                "Invalid inputs: Ensure Luminous Flux, Utilisation Factor, " +
                "and Maintenance Factor are valid numbers."
            );
        }
        
        // Standard lighting calculation formula
        return Math.ceil(
            (E * roomLength * roomWidth) / 
            (flux * Uf * MF)
        );
    } catch (error) {
        if (error instanceof Error) {
            throw error;
        }
        throw new Error("Invalid Luminous Flux value. Please check the CSV file.");
    }
}

/**
 * Find utilization factor (Uf) by interpolating between values in the table.
 * Uf tables are provided by the manufacturer as part of the overall lighting report
 * 
 * @param {number} K - Room Cavity Index
 * @param {number} Rc - Ceiling reflectance (0-100)
 * @param {number} Rw - Walls reflectance (0-100)
 * @param {number} Rf - Floor reflectance (0-100)
 * @param {Array<Array<number|string>>} ufTable - 2D array containing utilization factors
 *                                                First column is K values, rest are reflectance combinations
 * @returns {number} Interpolated utilization factor
 * @throws {Error} For invalid inputs or missing data
 */
function interpolateUf(K, Rc, Rw, Rf, ufTable) {
    try {
        // Convert table to numeric values (assuming first column is K values)
        const kValues = ufTable.map(row => parseFloat(row[0])).filter(val => !isNaN(val));
        
        if (kValues.length === 0) {
            throw new Error("No valid K values found in the utilization factor table.");
        }
        
        // Get valid K value range from table
        const minK = Math.min(...kValues);
        const maxK = Math.max(...kValues);
        
        // Check K is within table's range
        if (K < minK || K > maxK) {
            throw new Error(
                `Room Cavity Index (K) must be between ${minK} and ${maxK}.`
            );
        }
        
        // Find all reflectance combinations in the table columns
        // Assuming column headers are in format "RcXX_RwXX_RfXX" or similar
        const reflectanceCombinations = {};
        const headers = ufTable[0] || []; // First row might be headers
        
        // If first row looks like headers, process them
        // Otherwise, assume columns 1+ are reflectance combinations
        for (let colIdx = 1; colIdx < headers.length; colIdx++) {
            const colName = String(headers[colIdx] || `col${colIdx}`);
            
            // Try to parse reflectance values from column name
            // Format: "RcXX_RwXX_RfXX" or similar
            if (colName.startsWith("Rc") || colName.includes("_")) {
                const parts = colName.split("_");
                if (parts.length === 3) {
                    try {
                        // Extract Rc, Rw, Rf values from column names
                        const rcVal = parseInt(parts[0].substring(2));
                        const rwVal = parseInt(parts[1].substring(2));
                        const rfVal = parseInt(parts[2].substring(2));
                        
                        if (!isNaN(rcVal) && !isNaN(rwVal) && !isNaN(rfVal)) {
                            reflectanceCombinations[colIdx] = { rc: rcVal, rw: rwVal, rf: rfVal };
                        }
                    } catch (e) {
                        // Skip invalid column names
                        continue;
                    }
                }
            }
        }
        
        // If no named columns found, create default combinations
        // This is a fallback for tables without proper headers
        if (Object.keys(reflectanceCombinations).length === 0) {
            // Create synthetic combinations - this is a simplified approach
            // In a real implementation, you'd need to know the actual column structure
            throw new Error("No valid reflectance columns found in the CSV file.");
        }
        
        // Find closest matching reflectance combinations
        const distances = [];
        for (const [colIdx, { rc: rcCsv, rw: rwCsv, rf: rfCsv }] of Object.entries(reflectanceCombinations)) {
            // Calculate "distance" between requested and available reflectances
            const distance = Math.abs(rcCsv - Rc) + Math.abs(rwCsv - Rw) + Math.abs(rfCsv - Rf);
            distances.push({ distance, colIdx: parseInt(colIdx) });
        }
        
        // Sort by distance to find closest matches
        distances.sort((a, b) => a.distance - b.distance);
        const col1 = distances[0].colIdx;  // Closest match
        const col2 = distances[1] ? distances[1].colIdx : col1;  // Second closest match (or same if only one)
        
        // Get all K values from the table (skip header row if present)
        const dataRows = ufTable.slice(1).filter(row => !isNaN(parseFloat(row[0])));
        const kValuesArray = dataRows.map(row => parseFloat(row[0]));
        
        // Find the K values that bracket our calculated K
        const lowerK = Math.max(...kValuesArray.filter(k => k <= K));
        const upperK = Math.min(...kValuesArray.filter(k => k >= K));
        
        // Helper function to get Uf value from table
        const getUfValue = (kVal, col) => {
            const row = dataRows.find(r => Math.abs(parseFloat(r[0]) - kVal) < 0.001);
            return row ? parseFloat(row[col]) : null;
        };
        
        // Handle exact match case
        let Uf1, Uf2;
        if (Math.abs(lowerK - upperK) < 0.001) {
            Uf1 = getUfValue(lowerK, col1);
            Uf2 = getUfValue(lowerK, col2);
        } else {
            // Interpolate between bracketing K values for both reflectance combinations
            const uf1Lower = getUfValue(lowerK, col1);
            const uf1Upper = getUfValue(upperK, col1);
            Uf1 = uf1Lower + (K - lowerK) * (uf1Upper - uf1Lower) / (upperK - lowerK);
            
            const uf2Lower = getUfValue(lowerK, col2);
            const uf2Upper = getUfValue(upperK, col2);
            Uf2 = uf2Lower + (K - lowerK) * (uf2Upper - uf2Lower) / (upperK - lowerK);
        }
        
        // Calculate weights based on how close reflectances are
        const diff1 = distances[0].distance;
        const diff2 = distances[1] ? distances[1].distance : diff1;
        const weight1 = 1 / (diff1 + 1e-9);  // Small number to avoid division by zero
        const weight2 = 1 / (diff2 + 1e-9);
        
        // Final Uf is weighted average of two closest reflectance combinations
        const Uf = (Uf1 * weight1 + Uf2 * weight2) / (weight1 + weight2);
        return Uf;
    } catch (error) {
        if (error instanceof Error) {
            throw new Error(`Error calculating Uf: ${error.message}`);
        }
        throw new Error(`Error calculating Uf: ${error}`);
    }
}

/**
 * Calculate length-to-width ratio of the room.
 * 
 * @param {number} roomLength - Room length in meters
 * @param {number} roomWidth - Room width in meters
 * @returns {number} Aspect ratio (length/width)
 */
function calculateAspectRatio(roomLength, roomWidth) {
    return roomLength / roomWidth;
}

/**
 * Calculate spacing between fixtures along one dimension.
 * 
 * @param {number} roomDim - Room dimension (length or width) in meters
 * @param {number} numFixtures - Number of fixtures along this dimension
 * @returns {number} Spacing between fixtures in meters
 */
function calculateSpacing(roomDim, numFixtures) {
    if (numFixtures <= 1) {
        return roomDim;  // Special case: Only one fixture uses full dimension
    }
    return roomDim / numFixtures;
}

/**
 * Calculate Spacing-to-Height Ratio (SHR).
 * 
 * @param {number} spacing - Distance between fixtures in meters
 * @param {number} mountingHeight - Fixture mounting height in meters
 * @returns {number} SHR value (or Infinity if invalid height)
 */
function calculateShr(spacing, mountingHeight) {
    if (mountingHeight <= 0) {
        return Infinity;  // Invalid mounting height
    }
    return spacing / mountingHeight;
}

/**
 * Find valid fixture arrangements meeting SHR and spacing requirements.
 * 
 * @param {number} numFixtures - Calculated number of fixtures needed
 * @param {number} aspectRatio - Room length-to-width ratio
 * @param {number} roomLength - Room length in meters
 * @param {number} roomWidth - Room width in meters
 * @param {number} mountingHeight - Fixture mounting height in meters
 * @param {number} shrNom - Nominal SHR value from metadata
 * @returns {Array<{even: Object|null, odd: Object|null}>} Object with even and odd array layouts
 */
function findValidArrays(numFixtures, aspectRatio, roomLength, 
                         roomWidth, mountingHeight, shrNom) {
    const validArrays = [];
    
    // Try different numbers of rows and columns
    const maxDim = numFixtures + 3;  // Don't try more than this
    
    for (let rows = 1; rows <= maxDim; rows++) {
        for (let cols = 1; cols <= maxDim; cols++) {
            // Skip combinations that don't provide enough fixtures
            if (rows * cols < numFixtures) {
                continue;
            }
            
            // Determine orientation based on room shape
            let alongLength, acrossWidth;
            if (aspectRatio >= 1) {  // Longer than wide
                alongLength = Math.max(rows, cols);
                acrossWidth = Math.min(rows, cols);
            } else {  // Wider than long
                alongLength = Math.min(rows, cols);
                acrossWidth = Math.max(rows, cols);
            }
            
            // Calculate spacing in both directions
            const spacingLength = calculateSpacing(roomLength, alongLength);
            const spacingWidth = calculateSpacing(roomWidth, acrossWidth);
            
            // Calculate SHR in both directions
            const shrLength = calculateShr(spacingLength, mountingHeight);
            const shrWidth = calculateShr(spacingWidth, mountingHeight);
            
            // Check if this arrangement meets SHR requirements
            const shrValid = (shrLength <= shrNom && shrWidth <= shrNom);
            
            // Check minimum spacing requirements with special cases:
            let spacingValid;
            if (alongLength === 1) {  // Single row along length
                spacingValid = acrossWidth > 1 ? spacingWidth >= MIN_SPACING : true;
            } else if (acrossWidth === 1) {  // Single column across width
                spacingValid = alongLength > 1 ? spacingLength >= MIN_SPACING : true;
            } else {  // Multiple rows and columns
                spacingValid = (spacingLength >= MIN_SPACING && spacingWidth >= MIN_SPACING);
            }
            
            // Only add if both SHR and spacing requirements are met
            if (shrValid && spacingValid) {
                validArrays.push({
                    array: [alongLength, acrossWidth],
                    spacingLength: spacingLength,
                    spacingWidth: spacingWidth,
                    shrLength: shrLength,
                    shrWidth: shrWidth,
                    fixtures: alongLength * acrossWidth,
                    parity: acrossWidth % 2 === 0 ? 'even' : 'odd'
                });
            }
        }
    }
    
    // Remove duplicate arrangements and sort by closest to target fixture count
    const uniqueArrays = [];
    const seen = new Set();
    const sortedArrays = validArrays.sort((a, b) => {
        const diffA = Math.abs(a.fixtures - numFixtures);
        const diffB = Math.abs(b.fixtures - numFixtures);
        if (diffA !== diffB) return diffA - diffB;
        return a.fixtures - b.fixtures;
    });
    
    for (const arr of sortedArrays) {
        const key = `${arr.array[0]},${arr.array[1]}`;
        if (!seen.has(key)) {
            seen.add(key);
            uniqueArrays.push(arr);
        }
    }
    
    // Find one even and one odd arrangement
    const evenArray = uniqueArrays.find(a => a.parity === 'even') || null;
    const oddArray = uniqueArrays.find(a => a.parity === 'odd') || null;
    
    return { even: evenArray, odd: oddArray };
}

/**
 * Calculate actual light level based on how many fixtures are actually used.
 * 
 * @param {number} E - Target illuminance in lux
 * @param {number} numFixtures - Calculated number of fixtures needed
 * @param {number} actualFixtures - Number of fixtures in the actual layout
 * @returns {number} Adjusted illuminance level in lux
 */
function calculateAdjustedLightLevel(E, numFixtures, actualFixtures) {
    return E * (actualFixtures / numFixtures);
}

/**
 * Format array information for display in results.
 * 
 * @param {Object|null} arrayData - Array data object or null
 * @param {number} E - Required illuminance
 * @param {number} numFixtures - Calculated number of fixtures
 * @returns {string} Formatted array information string
 */
function formatArray(arrayData, E, numFixtures) {
    if (!arrayData) {
        return "No valid array found (spacing or SHR constraints not met)";
    }
    
    const array = arrayData.array;
    const spacingLength = arrayData.spacingLength;
    const spacingWidth = arrayData.spacingWidth;
    const actualFixtures = arrayData.fixtures;
    const adjustedE = calculateAdjustedLightLevel(E, numFixtures, actualFixtures);
    
    // Check spacing against minimum requirements
    const spacingStatus = [];
    if (array[0] > 1 && spacingLength < MIN_SPACING) {
        spacingStatus.push(`Length spacing < ${MIN_SPACING}m`);
    }
    if (array[1] > 1 && spacingWidth < MIN_SPACING) {
        spacingStatus.push(`Width spacing < ${MIN_SPACING}m`);
    }
    
    const spacingNote = spacingStatus.length === 0 
        ? " | Spacing OK" 
        : " | Spacing issues: " + spacingStatus.join(", ");
    
    return (
        `${array[0]} along length, ${array[1]} across width | ` +
        `Spacing: ${spacingLength.toFixed(2)}m (L), ${spacingWidth.toFixed(2)}m (W)${spacingNote} | ` +
        `SHR: ${arrayData.shrLength.toFixed(2)} (L), ${arrayData.shrWidth.toFixed(2)} (W) | ` +
        `Fixtures: ${actualFixtures}, Lux: ${adjustedE.toFixed(0)}`
    );
}

// ==============================================
// MAIN CALCULATION FUNCTION
// ==============================================

/**
 * Main function that performs all calculations and returns results.
 * This is the JavaScript equivalent of the Python calculate_and_display() function.
 * 
 * @param {Object} inputs - Input parameters object containing:
 *   - roomLength: Room length in meters
 *   - roomWidth: Room width in meters
 *   - roomHeight: Room height in meters
 *   - workingPlaneHeight: Working plane height in meters (default: 3)
 *   - suspensionDistance: Suspension distance in meters (default: 0)
 *   - ceilingReflectance: Ceiling reflectance (0-100, default: 0)
 *   - wallsReflectance: Walls reflectance (0-100, default: 0)
 *   - floorReflectance: Floor reflectance (0-100, default: 0)
 *   - requiredIlluminance: Required illuminance in lux (default: 3)
 *   - maintenanceFactor: Maintenance factor (0-1, default: 0.8)
 *   - luminousFlux: Luminous flux in lumens
 *   - wattage: Wattage in watts
 *   - shrNom: SHRNOM value from CSV
 *   - shrNomModified: Modified SHRNOM value
 *   - fixtureName: Name of the fixture
 *   - ufTable: Utilization factor table (2D array)
 * @returns {Object} Results object containing:
 *   - success: Boolean indicating if calculation succeeded
 *   - error: Error message if calculation failed
 *   - results: Array of result entries [label, value]
 *   - calculations: Object with calculated values (K, Uf, numFixtures, etc.)
 *   - arrays: Object with even and odd array layouts
 */
export function calculateAndDisplay(inputs) {
    try {
        // Validate all input values
        const roomLength = validateInput(inputs.roomLength, "Room Length", 0.1);
        const roomWidth = validateInput(inputs.roomWidth, "Room Width", 0.1);
        const roomHeight = validateInput(inputs.roomHeight, "Room Height", 0.1);
        const workingPlaneHeight = validateInput(
            inputs.workingPlaneHeight ?? 3, 
            "Working Plane Height", 
            0.1
        );
        const suspensionDistance = validateInput(
            inputs.suspensionDistance ?? 0, 
            "Suspension Distance", 
            0
        );
        const ceilingReflectance = validateInput(
            inputs.ceilingReflectance ?? 0, 
            "Ceiling Reflectance", 
            0, 
            100
        );
        const wallsReflectance = validateInput(
            inputs.wallsReflectance ?? 0, 
            "Walls Reflectance", 
            0, 
            100
        );
        const floorReflectance = validateInput(
            inputs.floorReflectance ?? 0, 
            "Floor Reflectance", 
            0, 
            100
        );
        const E = validateInput(inputs.requiredIlluminance ?? 3, "Required Illuminance", 0);
        const MF = validateInput(inputs.maintenanceFactor ?? 0.8, "Maintenance Factor", 0, 1);
        
        // Get values from the loaded CSV file/metadata
        const luminousFluxValue = parseFloat(inputs.luminousFlux);
        const wattageValue = parseFloat(inputs.wattage);
        const shrNomValue = inputs.shrNomModified || inputs.shrNom;
        
        if (isNaN(luminousFluxValue) || isNaN(wattageValue)) {
            throw new Error("Invalid luminous flux or wattage values from CSV file.");
        }
        
        // Perform all calculations
        const K = calculateRoomCavityIndex(
            roomLength, 
            roomWidth, 
            roomHeight, 
            workingPlaneHeight, 
            suspensionDistance
        );
        
        const Uf = interpolateUf(
            K, 
            ceilingReflectance, 
            wallsReflectance, 
            floorReflectance, 
            inputs.ufTable || []
        );
        
        const numFixtures = calculateNumberOfFixtures(
            E, 
            roomLength, 
            roomWidth, 
            luminousFluxValue, 
            Uf, 
            MF
        );
        
        // Calculate mounting height (distance from work plane to fixtures)
        const mountingHeight = (roomHeight - workingPlaneHeight) - suspensionDistance;
        if (mountingHeight <= 0) {
            throw new Error(
                "Invalid mounting height (check room height and suspension distance)"
            );
        }
        
        // Find valid fixture arrangements
        const aspectRatio = calculateAspectRatio(roomLength, roomWidth);
        const { even: evenArray, odd: oddArray } = findValidArrays(
            numFixtures, 
            aspectRatio, 
            roomLength, 
            roomWidth, 
            mountingHeight, 
            shrNomValue
        );
        
        // Prepare all results for display
        const results = [
            ["Fixture Name", inputs.fixtureName || "N/A"],
            ["Luminous Flux", `${luminousFluxValue.toFixed(0)} lumens`],
            ["Wattage", `${wattageValue.toFixed(0)} W`],
            ["SHRNOM (CSV)", `${inputs.shrNom?.toFixed(2) || "N/A"}`],
            ["SHRNOM (Modified)", `${shrNomValue.toFixed(2)}`],
            ["Minimum Spacing", `${MIN_SPACING} m (hard-coded)`],
            ["Room Length", `${roomLength.toFixed(1)} m`],
            ["Room Width", `${roomWidth.toFixed(1)} m`],
            ["Room Height", `${roomHeight.toFixed(1)} m`],
            ["Working Plane Height", `${workingPlaneHeight.toFixed(1)} m`],
            ["Suspension Distance", `${suspensionDistance.toFixed(1)} m`],
            ["Mounting Height", `${mountingHeight.toFixed(1)} m`],
            ["Ceiling Reflectance", `${ceilingReflectance.toFixed(0)} %`],
            ["Walls Reflectance", `${wallsReflectance.toFixed(0)} %`],
            ["Floor Reflectance", `${floorReflectance.toFixed(0)} %`],
            ["Required Lux Level", `${E.toFixed(0)} lux`],
            ["Maintenance Factor", `${MF.toFixed(2)}`],
            ["Room Cavity Index (K)", `${K.toFixed(2)}`],
            ["Utilisation Factor (Uf)", `${Uf.toFixed(2)}`],
            ["Number of Fixtures", `${numFixtures}`],
            ["Valid Array (Even)", formatArray(evenArray, E, numFixtures)],
            ["Valid Array (Odd)", formatArray(oddArray, E, numFixtures)]
        ];
        
        return {
            success: true,
            error: null,
            results: results,
            calculations: {
                K: K,
                Uf: Uf,
                numFixtures: numFixtures,
                mountingHeight: mountingHeight,
                aspectRatio: aspectRatio
            },
            arrays: {
                even: evenArray,
                odd: oddArray
            }
        };
        
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : String(error),
            results: null,
            calculations: null,
            arrays: null
        };
    }
}

// Export helper functions for use in other modules
export {
    validateInput,
    calculateRoomCavityIndex,
    calculateNumberOfFixtures,
    interpolateUf,
    calculateAspectRatio,
    calculateSpacing,
    calculateShr,
    findValidArrays,
    calculateAdjustedLightLevel,
    formatArray,
    SHR_FACTOR,
    MIN_SPACING
};

