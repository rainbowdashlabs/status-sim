const backendHost = import.meta.env.VITE_BACKEND_HOST ?? window.location.hostname;
const backendPort = import.meta.env.VITE_BACKEND_PORT ?? window.location.port;
const backendProtocol = import.meta.env.VITE_BACKEND_PROTOCOL ?? window.location.protocol;
const backendPortPart = backendPort ? `:${backendPort}` : '';

const backendBaseUrl = `${backendProtocol}//${backendHost}${backendPortPart}`;
const backendWsProtocol = backendProtocol === 'https:' ? 'wss:' : 'ws:';
const backendWsBaseUrl = `${backendWsProtocol}//${backendHost}${backendPortPart}`;

export { backendBaseUrl, backendWsBaseUrl };