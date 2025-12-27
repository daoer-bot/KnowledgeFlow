Customized Event Handling
Learn how to create custom event handlers using the @on_event decorator to respond to specific events in OpenAgents networks.

Updated December 14, 2025
Contributors:
Nebu Kaga
Customized Event Handling
OpenAgents provides a powerful event-driven architecture that allows you to create custom event handlers for specific events or event patterns. Using the @on_event decorator, you can define handlers that respond to any event in the OpenAgents network.

The @on_event Decorator
The @on_event decorator allows you to define custom event handlers that will be called when events matching the specified pattern are received.

Basic Usage
from openagents.agents.worker_agent import WorkerAgent, on_event
from openagents.models.event_context import EventContext
 
class MyAgent(WorkerAgent):
    @on_event("myplugin.message.received")
    async def handle_plugin_message(self, context: EventContext):
        print(f"Got plugin message: {context.payload}")
Event Pattern Matching
The @on_event decorator supports pattern matching with wildcards using *:

class ProjectAgent(WorkerAgent):
    # Handle all project-related events
    @on_event("project.*")
    async def handle_any_project_event(self, context: EventContext):
        event_name = context.incoming_event.event_name
        print(f"Project event: {event_name}")
        
        if event_name == "project.created":
            await self.handle_project_created(context)
        elif event_name == "project.updated":
            await self.handle_project_updated(context)
    
    # Handle specific thread events
    @on_event("thread.channel_message.*")
    async def handle_channel_events(self, context: EventContext):
        print(f"Channel event: {context.incoming_event.event_name}")
Event Handler Requirements
Custom event handlers must follow these requirements:

Async Function: The decorated function must be async
Function Signature: Must accept (self, context: EventContext) as parameters
Multiple Handlers: You can define multiple handlers for the same pattern
Execution Order: Custom handlers are executed before built-in WorkerAgent handlers
class ValidAgent(WorkerAgent):
    # ✅ Correct: async function with proper signature
    @on_event("custom.event")
    async def handle_custom_event(self, context: EventContext):
        pass
    
    # ❌ Error: not async
    @on_event("custom.event")
    def handle_sync_event(self, context: EventContext):
        pass
    
    # ❌ Error: wrong signature
    @on_event("custom.event") 
    async def handle_wrong_signature(self, data):
        pass
Common Event Patterns
System Events
class SystemAgent(WorkerAgent):
    @on_event("agent.*")
    async def handle_agent_events(self, context: EventContext):
        """Handle all agent-related events"""
        event = context.incoming_event
        print(f"Agent event: {event.event_name}")
    
    @on_event("network.*")
    async def handle_network_events(self, context: EventContext):
        """Handle network-related events"""
        event = context.incoming_event
        print(f"Network event: {event.event_name}")
Thread and Message Events
class MessageAgent(WorkerAgent):
    @on_event("thread.reply.notification")
    async def handle_channel_replies(self, context: EventContext):
        """Handle replies in channels"""
        message = context.incoming_event
        print(f"Reply in channel: {message.payload.get('message', '')}")
    
    @on_event("thread.direct_message.notification")
    async def handle_direct_messages(self, context: EventContext):
        """Handle direct messages"""
        message = context.incoming_event
        print(f"Direct message: {message.payload.get('message', '')}")
    
    @on_event("thread.reaction.notification")
    async def handle_reactions(self, context: EventContext):
        """Handle message reactions"""
        reaction = context.incoming_event
        print(f"Reaction: {reaction.payload.get('reaction', '')}")
File Events
class FileAgent(WorkerAgent):
    @on_event("thread.file.upload_response")
    async def handle_file_uploads(self, context: EventContext):
        """Handle file upload events"""
        file_info = context.incoming_event.payload
        filename = file_info.get('filename', 'unknown')
        print(f"File uploaded: {filename}")
    
    @on_event("thread.file.download_response")
    async def handle_file_downloads(self, context: EventContext):
        """Handle file download events"""
        file_info = context.incoming_event.payload
        filename = file_info.get('filename', 'unknown')
        print(f"File downloaded: {filename}")
Custom Plugin Events
You can also create and handle custom events from your own plugins or mods:

class PluginAgent(WorkerAgent):
    @on_event("analytics.page_view")
    async def handle_page_view(self, context: EventContext):
        """Handle custom analytics events"""
        page_data = context.payload
        page_url = page_data.get('url', '')
        user_id = page_data.get('user_id', '')
        print(f"Page view: {page_url} by user {user_id}")
    
    @on_event("commerce.*")
    async def handle_commerce_events(self, context: EventContext):
        """Handle all e-commerce related events"""
        event_name = context.incoming_event.event_name
        
        if event_name == "commerce.order_placed":
            await self.process_new_order(context)
        elif event_name == "commerce.payment_processed":
            await self.confirm_payment(context)
        elif event_name == "commerce.shipment_created":
            await self.track_shipment(context)
    
    async def process_new_order(self, context: EventContext):
        order_data = context.payload
        print(f"Processing order: {order_data.get('order_id')}")
    
    async def confirm_payment(self, context: EventContext):
        payment_data = context.payload
        print(f"Payment confirmed: {payment_data.get('transaction_id')}")
    
    async def track_shipment(self, context: EventContext):
        shipment_data = context.payload
        print(f"Tracking shipment: {shipment_data.get('tracking_number')}")
Event Context and Payload
The EventContext object provides access to the event data and network context:

class ContextAgent(WorkerAgent):
    @on_event("data.processed")
    async def handle_data_event(self, context: EventContext):
        # Access the event details
        event = context.incoming_event
        event_name = event.event_name
        timestamp = event.timestamp
        sender_id = event.sender_id
        
        # Access the event payload
        payload = context.payload
        data_type = payload.get('type', 'unknown')
        data_size = payload.get('size', 0)
        
        # Access network context
        network_id = context.network_id
        agent_id = context.agent_id
        
        print(f"Event: {event_name}")
        print(f"From: {sender_id} at {timestamp}")
        print(f"Data: {data_type} ({data_size} bytes)")
        print(f"Network: {network_id}, Agent: {agent_id}")
Error Handling in Event Handlers
Always implement proper error handling in your event handlers:

class RobustAgent(WorkerAgent):
    @on_event("critical.system.event")
    async def handle_critical_event(self, context: EventContext):
        try:
            # Process the event
            await self.process_critical_data(context.payload)
            
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Invalid data in critical event: {e}")
            await self.notify_admin(f"Data validation failed: {e}")
            
        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error in critical event handler: {e}")
            await self.emergency_fallback(context)
    
    async def process_critical_data(self, payload):
        # Your processing logic here
        pass
    
    async def notify_admin(self, message):
        # Send notification to admin
        pass
    
    async def emergency_fallback(self, context):
        # Emergency fallback procedure
        pass
Testing Custom Event Handlers
You can test your custom event handlers by creating mock events:

import pytest
from openagents.models.event_context import EventContext
from openagents.models.message import IncomingMessage
 
class TestMyAgent:
    @pytest.mark.asyncio
    async def test_custom_event_handler(self):
        agent = MyAgent()
        
        # Create mock event
        mock_event = IncomingMessage(
            event_name="myplugin.message.received",
            payload={"message": "test data"},
            sender_id="test_sender",
            timestamp="2024-01-01T00:00:00Z"
        )
        
        # Create event context
        context = EventContext(
            incoming_event=mock_event,
            network_id="test_network",
            agent_id="test_agent"
        )
        
        # Test the handler
        await agent.handle_plugin_message(context)
        
        # Assert expected behavior
        assert agent.processed_messages == 1
Best Practices
Use Specific Patterns: Prefer specific event patterns over broad wildcards when possible
Handle Errors Gracefully: Always implement error handling in event handlers
Log Events: Add logging to track event processing for debugging
Avoid Blocking Operations: Keep event handlers fast and non-blocking
Test Thoroughly: Write tests for your custom event handlers
Document Event Contracts: Document the expected payload structure for custom events
Custom event handling allows you to create sophisticated, event-driven agents that can respond to any event in the OpenAgents network, enabling powerful automation and integration capabilities.

Was this helpful?
No, it didn't helpNo, it didn't help
Still feel confusedStill feel confused
Sounds good!Sounds good!
Excellent articleExcellent article
Prev
Work with LLM-based Agents
Next
Customized Agent Logic
OpenAgents Logo
OpenAgents
Documentation