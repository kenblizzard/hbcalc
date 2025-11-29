/**
 * Sample data for demonstration purposes.
 * In production, this data should be loaded from CSV files.
 */

// Common utilization factor table (same for all fixtures in this example)
// In production, each fixture would have its own Uf table from CSV
const COMMON_UF_TABLE = [
    // Header row
    ["K", "Rc80_Rw70_Rf20", "Rc80_Rw50_Rf20", "Rc80_Rw30_Rf20", 
     "Rc70_Rw70_Rf20", "Rc70_Rw50_Rf20", "Rc70_Rw30_Rf20", 
     "Rc50_Rw70_Rf20", "Rc50_Rw50_Rf20", "Rc50_Rw30_Rf20", "Rc0_Rw0_Rf0"],
    // Data rows
    [0.6, 0.57, 0.45, 0.38, 0.56, 0.45, 0.38, 0.55, 0.45, 0.38, 0.32],
    [0.8, 0.68, 0.57, 0.49, 0.67, 0.56, 0.49, 0.65, 0.55, 0.49, 0.42],
    [1.0, 0.77, 0.67, 0.60, 0.76, 0.66, 0.59, 0.74, 0.67, 0.59, 0.52],
    [1.25, 0.85, 0.75, 0.68, 0.84, 0.74, 0.68, 0.81, 0.73, 0.67, 0.60],
    [1.5, 0.90, 0.81, 0.74, 0.88, 0.80, 0.74, 0.86, 0.78, 0.73, 0.65],
    [2.0, 0.97, 0.89, 0.83, 0.95, 0.88, 0.82, 0.92, 0.86, 0.81, 0.73],
    [2.5, 1.01, 0.93, 0.88, 0.99, 0.92, 0.87, 0.95, 0.89, 0.85, 0.77],
    [3.0, 1.04, 0.98, 0.92, 1.02, 0.96, 0.91, 0.98, 0.93, 0.89, 0.81],
    [4.0, 1.07, 1.02, 0.98, 1.05, 1.00, 0.97, 1.01, 0.97, 0.94, 0.85],
    [5.0, 1.10, 1.05, 1.01, 1.07, 1.03, 1.00, 1.03, 1.00, 0.97, 0.88]
];

/**
 * Get fixture data based on product code.
 * Maps highbay product codes to their fixture specifications.
 * 
 * @param {string} productCode - Product code (e.g., "HCL-100-CW", "HCL-150-CW", "HCL-200-CW")
 * @returns {Object} Fixture data object with fixture information and Uf table
 */
export function getFixtureDataByProductCode(productCode) {
    const fixtureData = {
        "HCL-100-CW": {
            fixtureName: "Voltex HCL-100-CW 120deg High Bay",
            luminousFlux: 12000, // Approximate value for 100W
            wattage: 100,
            shrNom: 1.20,
            ufTable: COMMON_UF_TABLE
        },
        "HCL-150-CW": {
            fixtureName: "Voltex HCL-150-CW 120deg High Bay",
            luminousFlux: 19000,
            wattage: 150,
            shrNom: 1.25,
            ufTable: COMMON_UF_TABLE
        },
        "HCL-200-CW": {
            fixtureName: "Voltex HCL-200-CW 120deg High Bay",
            luminousFlux: 25000, // Approximate value for 200W
            wattage: 200,
            shrNom: 1.30,
            ufTable: COMMON_UF_TABLE
        }
    };

    return fixtureData[productCode] || null;
}

/**
 * Get sample utilization factor table and fixture data.
 * This is based on the HCL-150-CW-120deg fixture format.
 * 
 * @deprecated Use getFixtureDataByProductCode instead
 * @returns {Object} Sample data object with fixture information and Uf table
 */
export function getSampleUfTable() {
    return {
        fixtureName: "Voltex HCL-150-CW 120deg High Bay",
        luminousFlux: 19000,
        wattage: 150,
        shrNom: 1.25,
        ufTable: COMMON_UF_TABLE
    };
}

