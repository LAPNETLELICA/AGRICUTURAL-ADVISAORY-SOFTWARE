from engine.models.enums import DeliveryStatus
from integrations.sms import SMSSimulator


def test_simulator_delivers_to_virtual_inbox():
    simulator = SMSSimulator()
    receipt = simulator.send("virtual-1", "irish-potato", "Test crop advisory", "rec-1")
    assert receipt.status is DeliveryStatus.DELIVERED
    inbox = simulator.inbox("virtual-1")
    assert inbox == [receipt]
    assert simulator.inbox("unknown") == []


def test_simulator_returns_defensive_copies():
    simulator = SMSSimulator()
    simulator.send("virtual-1", "irish-potato", "Original")
    inbox = simulator.inbox("virtual-1")
    inbox.clear()
    assert len(simulator.inbox("virtual-1")) == 1
