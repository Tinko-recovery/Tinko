// Mobile Testing Configuration
// Replace the API_BASE constant in auth.js with this dynamic detection

const API_BASE = (() => {
  // Check if we're on mobile by looking at the hostname
  const hostname = window.location.hostname;
  
  // If accessing via mobile (IP address), use laptop's IP
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `http://192.168.31.62:8000`;
  }
  
  // For laptop testing
  return "http://127.0.0.1:8000";
})();

// OR - Simple version for testing
// Uncomment this line and comment out the above code:
// const API_BASE = "http://192.168.31.62:8000";

console.log('Using API Base:', API_BASE);
