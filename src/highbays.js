const HIGHBAYS = [
    {
        "productName": "100W LED High Bay Light - Cool White - with 90° lens",
        "productCode": "HCL-100-CW",
        "wattage": 100,
        "recommendedMinimumRoomHeightInMeters": 5,
        "recommendedMaximumRoomHeightInMeters": 6.99
    },
    {
        "productName": "150W LED High Bay Light - Cool White - with 90° lens",
        "productCode": "HCL-150-CW",
        "wattage": 150,
        "recommendedMinimumRoomHeightInMeters": 7,
        "recommendedMaximumRoomHeightInMeters": 8.99
    },
    {
        "productName": "200W LED High Bay Light - Cool White - with 90° lens",
        "productCode": "HCL-200-CW",
        "wattage": 200,
        "recommendedMinimumRoomHeightInMeters": 9,
        "recommendedMaximumRoomHeightInMeters": 12
    }
];

/**
 * Get recommended highbay fixture based on room height.
 * 
 * @param {number} roomHeightInMeters - Room height in meters
 * @returns {Object|null} Recommended highbay fixture object, or null if no match found
 * @throws {Error} If roomHeightInMeters is invalid (not a number or <= 0)
 * 
 * @example
 * const recommended = getRecommendedHighbay(7.5);
 * // Returns: { productName: "150W LED High Bay Light...", productCode: "HCL-150-CW", ... }
 */
export function getRecommendedHighbay(roomHeightInMeters) {
    // Validate input
    const height = parseFloat(roomHeightInMeters);
    
    if (isNaN(height) || height <= 0) {
        throw new Error(
            `Invalid room height: ${roomHeightInMeters}. Room height must be a positive number.`
        );
    }
    
    // Find the highbay fixture where room height falls within the recommended range
    const recommended = HIGHBAYS.find(highbay => {
        return height >= highbay.recommendedMinimumRoomHeightInMeters && 
               height <= highbay.recommendedMaximumRoomHeightInMeters;
    });
    
    // If no exact match found, return the closest option
    // For heights below minimum, return the smallest fixture
    // For heights above maximum, return the largest fixture
    if (!recommended) {
        if (height < HIGHBAYS[0].recommendedMinimumRoomHeightInMeters) {
            // Room height is below minimum recommended height
            // Return the smallest fixture as a fallback
            return HIGHBAYS[0];
        } else if (height > HIGHBAYS[HIGHBAYS.length - 1].recommendedMaximumRoomHeightInMeters) {
            // Room height is above maximum recommended height
            // Return the largest fixture as a fallback
            return HIGHBAYS[HIGHBAYS.length - 1];
        }
    }
    
    return recommended || null;
}

/**
 * Get all available highbay fixtures.
 * 
 * @returns {Array} Array of all highbay fixture objects
 */
export function getAllHighbays() {
    return HIGHBAYS;
}

// Export the HIGHBAYS array for direct access if needed
export { HIGHBAYS };