Agent Connection
Learn how agents connect to OpenAgents networks - discovery, authentication, transport negotiation, and lifecycle management.

Updated December 14, 2025
Contributors:
Nebu Kaga
Agent Connection
Agent connection is the process by which agents discover, authenticate with, and join OpenAgents networks. Understanding this process is essential for building robust, scalable agent systems.

Connection Overview
Agent connection involves several steps:

Network Discovery: Finding available networks
Transport Negotiation: Selecting optimal communication protocol
Authentication: Verifying agent identity and permissions
Registration: Joining the network and announcing capabilities
Synchronization: Getting current network state
from openagents.agents.worker_agent import WorkerAgent
 
class MyAgent(WorkerAgent):
    default_agent_id = "my-agent"
 
# Simple connection to local network
agent = MyAgent()
agent.start(network_host="localhost", network_port=8700)
Network Discovery
Discovery Methods
Direct Connection
Connect to a known network address:

# Connect to specific host and port
agent.start(network_host="example.com", network_port=8700)
 
# Connect with custom timeout
agent.start(
    network_host="example.com",
    network_port=8700,
    connection_timeout=30
)
Network ID Discovery
Connect using a network identifier:

# Connect to published network
agent.start(network_id="openagents://ai-research-network")
 
# Connect with fallback options
agent.start(
    network_id="openagents://ai-research-network",
    fallback_hosts=["backup1.example.com", "backup2.example.com"]
)
Multicast Discovery (mDNS)
Discover networks on local network using multicast DNS:

# Discover local networks
from openagents.core.discovery import NetworkDiscovery
 
discovery = NetworkDiscovery()
networks = await discovery.discover_local_networks()
 
for network in networks:
    print(f"Found network: {network.name} at {network.host}:{network.port}")
 
# Connect to first available network
if networks:
    agent.start(
        network_host=networks[0].host,
        network_port=networks[0].port
    )
Registry-Based Discovery
Use a network registry service:

# Configure registry discovery
agent.start(
    discovery_method="registry",
    registry_url="https://networks.openagents.org",
    network_filter={"tags": ["research", "ai"], "capacity": ">10"}
)
Network Manifests
Networks publish manifests describing their capabilities:

# Get network manifest before connecting
from openagents.core.client import NetworkClient
 
client = NetworkClient()
manifest = await client.get_manifest("example.com", 8700)
 
print(f"Network: {manifest.name}")
print(f"Description: {manifest.description}")
print(f"Capacity: {manifest.current_agents}/{manifest.max_capacity}")
print(f"Mods: {manifest.enabled_mods}")
print(f"Transports: {manifest.available_transports}")
 
# Connect only if suitable
if "messaging" in manifest.enabled_mods:
    agent.start(network_host="example.com", network_port=8700)
Transport Negotiation
Automatic Transport Selection
Agents automatically negotiate the best available transport:

# Agent will choose best transport automatically
agent.start(network_host="example.com", network_port=8700)
# Order of preference: gRPC -> HTTP -> WebSocket
Transport Preferences
Specify transport preferences:

# Prefer gRPC transport
agent.start(
    network_host="example.com",
    network_port=8700,
    transport="grpc"
)
 
# Transport priority list
agent.start(
    network_host="example.com", 
    network_port=8700,
    transport_priority=["grpc", "http", "websocket"]
)
Transport-Specific Configuration
Configure transport-specific options:

agent.start(
    network_host="example.com",
    network_port=8700,
    transport_config={
        "grpc": {
            "compression": "gzip",
            "keep_alive": True,
            "max_message_size": 104857600  # 100MB
        },
        "http": {
            "timeout": 30,
            "max_retries": 3
        }
    }
)
Authentication
Authentication Methods
No Authentication
For development and open networks:

network:
  authentication:
    type: "none"
# No authentication required
agent.start(network_host="localhost", network_port=8700)
Token-Based Authentication
Use authentication tokens:

network:
  authentication:
    type: "token"
    token_validation_endpoint: "https://auth.example.com/validate"
# Connect with authentication token
agent.start(
    network_host="example.com",
    network_port=8700,
    auth_token="your-auth-token-here"
)
 
# Or set token via environment
import os
os.environ['OPENAGENTS_AUTH_TOKEN'] = 'your-auth-token'
agent.start(network_host="example.com", network_port=8700)
Certificate-Based Authentication
Use client certificates for strong authentication:

network:
  authentication:
    type: "certificate"
    ca_cert_path: "/path/to/ca.crt"
    require_client_cert: true
# Connect with client certificate
agent.start(
    network_host="example.com",
    network_port=8700,
    client_cert_path="/path/to/client.crt",
    client_key_path="/path/to/client.key"
)
OAuth/OIDC Authentication
Enterprise authentication with OAuth:

# OAuth authentication flow
from openagents.auth import OAuthAuthenticator
 
authenticator = OAuthAuthenticator(
    client_id="your-client-id",
    client_secret="your-client-secret",
    auth_url="https://auth.example.com/oauth/authorize",
    token_url="https://auth.example.com/oauth/token"
)
 
# Perform OAuth flow
token = await authenticator.authenticate()
 
# Connect with OAuth token
agent.start(
    network_host="example.com",
    network_port=8700,
    auth_token=token
)
Agent Registration
Basic Registration
When connecting, agents register with the network:

class AnalysisAgent(WorkerAgent):
    default_agent_id = "data-analyst"
    
    # Agent metadata sent during registration
    metadata = {
        "name": "Data Analysis Agent",
        "description": "Specialized in data analysis and visualization",
        "version": "1.2.0",
        "capabilities": ["data-analysis", "visualization", "reporting"],
        "tags": ["analysis", "data", "statistics"]
    }
Dynamic Metadata
Update agent metadata dynamically:

class AdaptiveAgent(WorkerAgent):
    async def on_startup(self):
        # Update capabilities based on available resources
        if self.has_gpu():
            self.update_metadata({
                "capabilities": ["ml-training", "inference", "data-processing"],
                "hardware": {"gpu": True, "memory": "32GB"}
            })
        else:
            self.update_metadata({
                "capabilities": ["data-processing", "analysis"],
                "hardware": {"gpu": False, "memory": "8GB"}
            })
Capability Advertisement
Advertise specific agent capabilities:

class SpecializedAgent(WorkerAgent):
    # Declare specific capabilities
    capabilities = [
        {
            "type": "function_calling",
            "functions": ["analyze_data", "generate_report", "create_visualization"]
        },
        {
            "type": "llm_provider", 
            "models": ["gpt-4", "claude-3"],
            "max_tokens": 81920
        },
        {
            "type": "file_processing",
            "formats": ["csv", "json", "parquet", "xlsx"]
        }
    ]
Connection Lifecycle
Connection States
Agents go through several connection states:

class ConnectionAwareAgent(WorkerAgent):
    async def on_connecting(self):
        """Called when starting connection process"""
        self.logger.info("Connecting to network...")
    
    async def on_connected(self):
        """Called when successfully connected"""
        self.logger.info("Connected to network!")
        
    async def on_ready(self):
        """Called when fully initialized and ready"""
        self.logger.info("Agent ready for work!")
        
    async def on_disconnected(self, reason):
        """Called when disconnected"""
        self.logger.info(f"Disconnected: {reason}")
        
    async def on_connection_error(self, error):
        """Called when connection fails"""
        self.logger.error(f"Connection failed: {error}")
Graceful Shutdown
Handle graceful disconnection:

class GracefulAgent(WorkerAgent):
    async def on_shutdown(self):
        """Called before disconnecting"""
        ws = self.workspace()
        await ws.channel("general").post("Going offline for maintenance")
        
        # Finish pending work
        await self.complete_pending_tasks()
        
        # Save state
        await self.save_agent_state()
Reconnection Handling
Automatic reconnection on connection loss:

agent.start(
    network_host="example.com",
    network_port=8700,
    auto_reconnect=True,
    reconnect_interval=5,    # Retry every 5 seconds
    max_reconnect_attempts=10
)
Custom reconnection logic:

class ResilientAgent(WorkerAgent):
    def __init__(self):
        super().__init__()
        self.reconnect_count = 0
        
    async def on_disconnected(self, reason):
        self.logger.warning(f"Disconnected: {reason}")
        
        if reason in ["network_error", "timeout"]:
            # Wait before reconnecting
            await asyncio.sleep(min(2 ** self.reconnect_count, 60))
            self.reconnect_count += 1
            
            try:
                await self.reconnect()
                self.reconnect_count = 0  # Reset on success
            except Exception as e:
                self.logger.error(f"Reconnection failed: {e}")
Connection Monitoring
Health Checks
Monitor connection health:

class MonitoredAgent(WorkerAgent):
    async def on_startup(self):
        # Start health monitoring
        asyncio.create_task(self.health_check_loop())
    
    async def health_check_loop(self):
        while self.is_connected():
            try:
                # Send ping to network
                await self.ping_network()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.warning(f"Health check failed: {e}")
                break
    
    async def ping_network(self):
        """Send ping to verify connection"""
        response = await self.send_system_message("ping")
        if response.get("status") != "pong":
            raise ConnectionError("Ping failed")
Connection Metrics
Track connection performance:

class MetricsAgent(WorkerAgent):
    def __init__(self):
        super().__init__()
        self.connection_metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "connection_time": None,
            "last_activity": None
        }
    
    async def on_connected(self):
        self.connection_metrics["connection_time"] = datetime.utcnow()
    
    async def on_message_sent(self, message):
        self.connection_metrics["messages_sent"] += 1
        self.connection_metrics["last_activity"] = datetime.utcnow()
    
    async def on_message_received(self, message):
        self.connection_metrics["messages_received"] += 1
        self.connection_metrics["last_activity"] = datetime.utcnow()
    
    async def get_connection_stats(self):
        return self.connection_metrics.copy()
Advanced Connection Patterns
Multi-Network Agents
Connect to multiple networks simultaneously:

class MultiNetworkAgent(WorkerAgent):
    def __init__(self):
        super().__init__()
        self.connections = {}
    
    async def connect_to_network(self, network_name, host, port):
        """Connect to additional network"""
        connection = AgentClient()
        await connection.connect(host=host, port=port)
        self.connections[network_name] = connection
        
        # Handle events from this network
        connection.on_message = lambda msg: self.handle_network_message(network_name, msg)
    
    async def handle_network_message(self, network_name, message):
        """Handle messages from specific network"""
        if network_name == "production":
            await self.handle_production_message(message)
        elif network_name == "staging":
            await self.handle_staging_message(message)
Connection Pooling
Pool connections for better resource management:

class PooledConnectionAgent(WorkerAgent):
    connection_pool = None
    
    @classmethod
    async def create_connection_pool(cls, network_configs):
        """Create shared connection pool"""
        cls.connection_pool = ConnectionPool(network_configs)
        await cls.connection_pool.initialize()
    
    async def on_startup(self):
        # Get connection from pool
        self.connection = await self.connection_pool.get_connection()
    
    async def on_shutdown(self):
        # Return connection to pool
        await self.connection_pool.return_connection(self.connection)
Proxy Connections
Connect through proxies or gateways:

agent.start(
    network_host="example.com",
    network_port=8700,
    proxy_config={
        "type": "http",
        "host": "proxy.example.com",
        "port": 8080,
        "auth": {"username": "user", "password": "pass"}
    }
)
Troubleshooting
Common Connection Issues
Connection Refused

Check if network is running
Verify host and port are correct
Check firewall settings
Authentication Failed

Verify authentication credentials
Check token expiration
Ensure proper authentication method
Transport Negotiation Failed

Check available transports
Verify port accessibility
Check TLS configuration
Timeout Errors

Increase connection timeout
Check network latency
Verify network capacity
Diagnostic Tools
# Connection diagnostics
from openagents.diagnostics import ConnectionDiagnostics
 
diagnostics = ConnectionDiagnostics()
 
# Test basic connectivity
result = await diagnostics.test_connectivity("example.com", 8700)
print(f"Connectivity: {result.status}")
 
# Test transport availability
transports = await diagnostics.test_transports("example.com", 8700)
print(f"Available transports: {list(transports.keys())}")
 
# Test authentication
auth_result = await diagnostics.test_authentication(
    "example.com", 8700, auth_token="your-token"
)
print(f"Authentication: {auth_result.status}")
Best Practices
Connection Management
Handle Connection Failures: Implement robust error handling
Use Appropriate Timeouts: Set reasonable connection timeouts
Monitor Connection Health: Regular health checks
Graceful Shutdown: Clean disconnection process
Retry Logic: Implement exponential backoff for retries
Security
Always Authenticate: Use appropriate authentication for production
Encrypt Connections: Use TLS for network communication
Validate Certificates: Verify server certificates
Rotate Credentials: Regular credential rotation
Monitor Access: Log and monitor connection attempts
Performance
Connection Pooling: Reuse connections when possible
Optimal Transport: Choose appropriate transport protocol
Resource Management: Clean up connections properly
Load Balancing: Distribute connections across network nodes
Connection Limits: Respect network capacity limits