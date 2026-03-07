// *********************************************************************
// ATTENTION (is all you need): this file is (almost) fully AI-generated
// *********************************************************************

const protocol = window.location.protocol;
const hostname = window.location.hostname;
const port = window.location.port;

let apiPort;
if (port) {
    apiPort = port;
} else {
    apiPort = '8011';
}

// Construct the API base URL and store it in window.API_CONFIG
window.API_CONFIG = {
    API_BASE: `${protocol}//${hostname}:${apiPort}/api`
};
