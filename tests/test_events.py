"""
Event System Tests

Tests for EventEmitter, EventType, and StateChangeEvent
"""

import pytest
from datetime import datetime
from src.events import EventEmitter, EventType, StateChangeEvent


# ============================================================================
# EventType Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestEventType:
    """Tests for EventType enum"""

    def test_event_type_values(self):
        """Test all EventType enum values exist"""
        assert EventType.MODEL_CHANGED.value == "model_changed"
        assert EventType.WORKSPACE_CHANGED.value == "workspace_changed"
        assert EventType.BRANCH_CHANGED.value == "branch_changed"
        assert EventType.CONTEXT_THRESHOLD.value == "context_threshold"
        assert EventType.STATE_UPDATED.value == "state_updated"

    def test_event_type_count(self):
        """Test expected number of event types"""
        event_types = list(EventType)
        assert len(event_types) == 5

    def test_event_type_unique_values(self):
        """Test all event type values are unique"""
        values = [et.value for et in EventType]
        assert len(values) == len(set(values))

    def test_event_type_comparison(self):
        """Test event type comparison"""
        assert EventType.MODEL_CHANGED == EventType.MODEL_CHANGED
        assert EventType.MODEL_CHANGED != EventType.BRANCH_CHANGED


# ============================================================================
# StateChangeEvent Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestStateChangeEvent:
    """Tests for StateChangeEvent dataclass"""

    def test_event_creation_basic(self):
        """Test basic StateChangeEvent creation"""
        event = StateChangeEvent(
            event_type=EventType.BRANCH_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="main",
            new_value="develop"
        )

        assert event.event_type == EventType.BRANCH_CHANGED
        assert event.old_value == "main"
        assert event.new_value == "develop"
        assert event.metadata is None

    def test_event_creation_with_metadata(self):
        """Test StateChangeEvent with metadata"""
        metadata = {"workspace": "test-project", "user": "testuser"}
        event = StateChangeEvent(
            event_type=EventType.MODEL_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="Claude",
            new_value="GPT-4",
            metadata=metadata
        )

        assert event.metadata == metadata
        assert event.metadata["workspace"] == "test-project"

    def test_event_to_dict(self):
        """Test StateChangeEvent to_dict conversion"""
        timestamp = datetime.utcnow().isoformat()
        metadata = {"key": "value"}
        event = StateChangeEvent(
            event_type=EventType.CONTEXT_THRESHOLD,
            timestamp=timestamp,
            old_value=50,
            new_value=75,
            metadata=metadata
        )

        result = event.to_dict()

        assert isinstance(result, dict)
        assert result["event_type"] == "context_threshold"
        assert result["timestamp"] == timestamp
        assert result["old_value"] == 50
        assert result["new_value"] == 75
        assert result["metadata"] == metadata

    def test_event_to_dict_no_metadata(self):
        """Test to_dict with no metadata"""
        event = StateChangeEvent(
            event_type=EventType.STATE_UPDATED,
            timestamp=datetime.utcnow().isoformat(),
            old_value=None,
            new_value="updated"
        )

        result = event.to_dict()

        assert result["metadata"] == {}

    def test_event_with_none_values(self):
        """Test event with None old/new values"""
        event = StateChangeEvent(
            event_type=EventType.WORKSPACE_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value=None,
            new_value="new-workspace"
        )

        assert event.old_value is None
        assert event.new_value == "new-workspace"

    def test_event_with_complex_values(self):
        """Test event with complex object values"""
        old_state = {"branch": "main", "commits": 10}
        new_state = {"branch": "develop", "commits": 15}

        event = StateChangeEvent(
            event_type=EventType.BRANCH_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value=old_state,
            new_value=new_state
        )

        assert event.old_value["branch"] == "main"
        assert event.new_value["branch"] == "develop"


# ============================================================================
# EventEmitter Initialization Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestEventEmitterInitialization:
    """Tests for EventEmitter initialization"""

    def test_emitter_initialization(self):
        """Test EventEmitter initializes correctly"""
        emitter = EventEmitter()

        assert emitter is not None
        assert hasattr(emitter, '_handlers')

    def test_emitter_has_all_event_handlers(self):
        """Test emitter initializes handlers for all event types"""
        emitter = EventEmitter()

        for event_type in EventType:
            assert event_type in emitter._handlers
            assert isinstance(emitter._handlers[event_type], list)
            assert len(emitter._handlers[event_type]) == 0

    def test_multiple_emitter_instances_independent(self):
        """Test multiple emitter instances are independent"""
        emitter1 = EventEmitter()
        emitter2 = EventEmitter()

        # Register handler on emitter1
        def handler(event):
            pass

        emitter1.on(EventType.MODEL_CHANGED, handler)

        # emitter2 should not have the handler
        assert len(emitter1._handlers[EventType.MODEL_CHANGED]) == 1
        assert len(emitter2._handlers[EventType.MODEL_CHANGED]) == 0


# ============================================================================
# EventEmitter Registration Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestEventEmitterRegistration:
    """Tests for event handler registration"""

    def test_register_single_handler(self, event_emitter, callback_tracker):
        """Test registering a single event handler"""
        event_emitter.on(EventType.MODEL_CHANGED, callback_tracker.callback)

        handlers = event_emitter._handlers[EventType.MODEL_CHANGED]
        assert len(handlers) == 1
        assert callback_tracker.callback in handlers

    def test_register_multiple_handlers_same_event(self, event_emitter):
        """Test registering multiple handlers for same event"""
        def handler1(event):
            pass

        def handler2(event):
            pass

        def handler3(event):
            pass

        event_emitter.on(EventType.BRANCH_CHANGED, handler1)
        event_emitter.on(EventType.BRANCH_CHANGED, handler2)
        event_emitter.on(EventType.BRANCH_CHANGED, handler3)

        handlers = event_emitter._handlers[EventType.BRANCH_CHANGED]
        assert len(handlers) == 3
        assert handler1 in handlers
        assert handler2 in handlers
        assert handler3 in handlers

    def test_register_same_handler_multiple_events(self, event_emitter):
        """Test registering same handler for multiple events"""
        def universal_handler(event):
            pass

        event_emitter.on(EventType.MODEL_CHANGED, universal_handler)
        event_emitter.on(EventType.BRANCH_CHANGED, universal_handler)
        event_emitter.on(EventType.WORKSPACE_CHANGED, universal_handler)

        assert universal_handler in event_emitter._handlers[EventType.MODEL_CHANGED]
        assert universal_handler in event_emitter._handlers[EventType.BRANCH_CHANGED]
        assert universal_handler in event_emitter._handlers[EventType.WORKSPACE_CHANGED]

    def test_register_lambda_handler(self, event_emitter):
        """Test registering lambda as handler"""
        lambda_handler = lambda event: None

        event_emitter.on(EventType.STATE_UPDATED, lambda_handler)

        handlers = event_emitter._handlers[EventType.STATE_UPDATED]
        assert len(handlers) == 1


# ============================================================================
# EventEmitter Emission Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestEventEmitterEmission:
    """Tests for event emission"""

    def test_emit_calls_handler(self, event_emitter, callback_tracker):
        """Test emit calls registered handler"""
        event_emitter.on(EventType.MODEL_CHANGED, callback_tracker.callback)

        event = StateChangeEvent(
            event_type=EventType.MODEL_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="Claude",
            new_value="GPT-4"
        )

        event_emitter.emit(event)

        callback_tracker.assert_called_once()

    def test_emit_passes_event_to_handler(self, event_emitter):
        """Test emit passes event object to handler"""
        received_events = []

        def handler(event):
            received_events.append(event)

        event_emitter.on(EventType.BRANCH_CHANGED, handler)

        event = StateChangeEvent(
            event_type=EventType.BRANCH_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="main",
            new_value="develop"
        )

        event_emitter.emit(event)

        assert len(received_events) == 1
        assert received_events[0] == event

    def test_emit_calls_all_handlers(self, event_emitter):
        """Test emit calls all registered handlers"""
        call_count = {"count": 0}

        def handler1(event):
            call_count["count"] += 1

        def handler2(event):
            call_count["count"] += 1

        def handler3(event):
            call_count["count"] += 1

        event_emitter.on(EventType.WORKSPACE_CHANGED, handler1)
        event_emitter.on(EventType.WORKSPACE_CHANGED, handler2)
        event_emitter.on(EventType.WORKSPACE_CHANGED, handler3)

        event = StateChangeEvent(
            event_type=EventType.WORKSPACE_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="old-workspace",
            new_value="new-workspace"
        )

        event_emitter.emit(event)

        assert call_count["count"] == 3

    def test_emit_no_handlers_no_error(self, event_emitter):
        """Test emit with no handlers doesn't raise error"""
        event = StateChangeEvent(
            event_type=EventType.CONTEXT_THRESHOLD,
            timestamp=datetime.utcnow().isoformat(),
            old_value=50,
            new_value=80
        )

        # Should not raise
        event_emitter.emit(event)

    def test_emit_only_calls_matching_event_handlers(self, event_emitter):
        """Test emit only calls handlers for matching event type"""
        model_calls = []
        branch_calls = []

        def model_handler(event):
            model_calls.append(event)

        def branch_handler(event):
            branch_calls.append(event)

        event_emitter.on(EventType.MODEL_CHANGED, model_handler)
        event_emitter.on(EventType.BRANCH_CHANGED, branch_handler)

        event = StateChangeEvent(
            event_type=EventType.MODEL_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="Claude",
            new_value="GPT-4"
        )

        event_emitter.emit(event)

        assert len(model_calls) == 1
        assert len(branch_calls) == 0


# ============================================================================
# EventEmitter Unregistration Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestEventEmitterUnregistration:
    """Tests for event handler unregistration"""

    def test_unregister_handler(self, event_emitter, callback_tracker):
        """Test unregistering a handler"""
        event_emitter.on(EventType.STATE_UPDATED, callback_tracker.callback)
        assert len(event_emitter._handlers[EventType.STATE_UPDATED]) == 1

        event_emitter.off(EventType.STATE_UPDATED, callback_tracker.callback)
        assert len(event_emitter._handlers[EventType.STATE_UPDATED]) == 0

    def test_unregister_one_of_multiple_handlers(self, event_emitter):
        """Test unregistering one handler among multiple"""
        def handler1(event):
            pass

        def handler2(event):
            pass

        event_emitter.on(EventType.MODEL_CHANGED, handler1)
        event_emitter.on(EventType.MODEL_CHANGED, handler2)

        event_emitter.off(EventType.MODEL_CHANGED, handler1)

        handlers = event_emitter._handlers[EventType.MODEL_CHANGED]
        assert len(handlers) == 1
        assert handler2 in handlers
        assert handler1 not in handlers

    def test_unregister_nonexistent_handler_no_error(self, event_emitter):
        """Test unregistering non-existent handler doesn't raise error"""
        def handler(event):
            pass

        # Should not raise
        event_emitter.off(EventType.BRANCH_CHANGED, handler)

    def test_unregister_after_emit(self, event_emitter, callback_tracker):
        """Test handler can be unregistered after being called"""
        event_emitter.on(EventType.MODEL_CHANGED, callback_tracker.callback)

        # Emit event
        event = StateChangeEvent(
            event_type=EventType.MODEL_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="Claude",
            new_value="GPT-4"
        )
        event_emitter.emit(event)
        callback_tracker.assert_called_once()

        # Unregister
        event_emitter.off(EventType.MODEL_CHANGED, callback_tracker.callback)

        # Emit again - should not be called
        event_emitter.emit(event)
        callback_tracker.assert_called_once()  # Still only called once


# ============================================================================
# EventEmitter Clear Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestEventEmitterClear:
    """Tests for clearing event handlers"""

    def test_clear_specific_event_type(self, event_emitter):
        """Test clearing handlers for specific event type"""
        def handler1(event):
            pass

        def handler2(event):
            pass

        event_emitter.on(EventType.BRANCH_CHANGED, handler1)
        event_emitter.on(EventType.MODEL_CHANGED, handler2)

        event_emitter.clear(EventType.BRANCH_CHANGED)

        assert len(event_emitter._handlers[EventType.BRANCH_CHANGED]) == 0
        assert len(event_emitter._handlers[EventType.MODEL_CHANGED]) == 1

    def test_clear_all_handlers(self, event_emitter):
        """Test clearing all handlers"""
        def handler(event):
            pass

        # Register handlers for multiple events
        event_emitter.on(EventType.MODEL_CHANGED, handler)
        event_emitter.on(EventType.BRANCH_CHANGED, handler)
        event_emitter.on(EventType.WORKSPACE_CHANGED, handler)
        event_emitter.on(EventType.CONTEXT_THRESHOLD, handler)

        event_emitter.clear()

        # All should be cleared
        for event_type in EventType:
            assert len(event_emitter._handlers[event_type]) == 0

    def test_clear_empty_handlers_no_error(self, event_emitter):
        """Test clearing when no handlers registered"""
        # Should not raise
        event_emitter.clear(EventType.STATE_UPDATED)
        event_emitter.clear()


# ============================================================================
# EventEmitter Error Handling Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.events
class TestEventEmitterErrorHandling:
    """Tests for error handling in event emission"""

    def test_handler_exception_doesnt_stop_other_handlers(self, event_emitter, capsys):
        """Test handler exception doesn't prevent other handlers from running"""
        call_order = []

        def failing_handler(event):
            call_order.append("failing")
            raise ValueError("Handler error")

        def working_handler(event):
            call_order.append("working")

        event_emitter.on(EventType.MODEL_CHANGED, failing_handler)
        event_emitter.on(EventType.MODEL_CHANGED, working_handler)

        event = StateChangeEvent(
            event_type=EventType.MODEL_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="Claude",
            new_value="GPT-4"
        )

        event_emitter.emit(event)

        # Both handlers should have been called
        assert "failing" in call_order
        assert "working" in call_order

        # Error message should be printed
        captured = capsys.readouterr()
        assert "Error in event handler" in captured.out

    def test_multiple_handler_exceptions(self, event_emitter, capsys):
        """Test multiple handler exceptions are all caught"""
        def failing_handler1(event):
            raise ValueError("Error 1")

        def failing_handler2(event):
            raise TypeError("Error 2")

        event_emitter.on(EventType.BRANCH_CHANGED, failing_handler1)
        event_emitter.on(EventType.BRANCH_CHANGED, failing_handler2)

        event = StateChangeEvent(
            event_type=EventType.BRANCH_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="main",
            new_value="develop"
        )

        # Should not raise
        event_emitter.emit(event)

        # Both errors should be logged
        captured = capsys.readouterr()
        assert captured.out.count("Error in event handler") == 2


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.events
class TestEventEmitterIntegration:
    """Integration tests for event system"""

    def test_complete_event_lifecycle(self, event_emitter):
        """Test complete event lifecycle: register, emit, unregister"""
        events_received = []

        def handler(event):
            events_received.append(event)

        # Register
        event_emitter.on(EventType.MODEL_CHANGED, handler)

        # Emit multiple events
        for i in range(3):
            event = StateChangeEvent(
                event_type=EventType.MODEL_CHANGED,
                timestamp=datetime.utcnow().isoformat(),
                old_value=f"model-{i}",
                new_value=f"model-{i+1}"
            )
            event_emitter.emit(event)

        assert len(events_received) == 3

        # Unregister
        event_emitter.off(EventType.MODEL_CHANGED, handler)

        # Emit again - should not receive
        event = StateChangeEvent(
            event_type=EventType.MODEL_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="model-x",
            new_value="model-y"
        )
        event_emitter.emit(event)

        assert len(events_received) == 3  # Still 3

    def test_event_chain_reaction(self, event_emitter):
        """Test handler can emit another event (chain reaction)"""
        events_log = []

        def model_handler(event):
            events_log.append(("model", event.new_value))
            # Emit workspace change as consequence
            workspace_event = StateChangeEvent(
                event_type=EventType.WORKSPACE_CHANGED,
                timestamp=datetime.utcnow().isoformat(),
                old_value="old-workspace",
                new_value="new-workspace"
            )
            event_emitter.emit(workspace_event)

        def workspace_handler(event):
            events_log.append(("workspace", event.new_value))

        event_emitter.on(EventType.MODEL_CHANGED, model_handler)
        event_emitter.on(EventType.WORKSPACE_CHANGED, workspace_handler)

        # Trigger initial event
        event = StateChangeEvent(
            event_type=EventType.MODEL_CHANGED,
            timestamp=datetime.utcnow().isoformat(),
            old_value="Claude",
            new_value="GPT-4"
        )
        event_emitter.emit(event)

        # Should have both events logged
        assert len(events_log) == 2
        assert events_log[0] == ("model", "GPT-4")
        assert events_log[1] == ("workspace", "new-workspace")

    def test_state_change_event_creation_from_sample(self, sample_state_change_event):
        """Test using sample state change event fixture"""
        event = sample_state_change_event

        assert event.event_type == EventType.BRANCH_CHANGED
        assert event.old_value == "main"
        assert event.new_value == "feature-branch"
        assert "workspace" in event.metadata

        # Can be serialized
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "branch_changed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
