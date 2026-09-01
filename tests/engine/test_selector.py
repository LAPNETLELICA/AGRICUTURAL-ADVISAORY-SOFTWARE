from engine.advisory.selector import CropTreeSelector
from engine.models.enums import Channel, TreeId


def test_selector_is_crop_rooted_and_dynamic(context):
    selected = CropTreeSelector().select(context)
    assert selected[0] is TreeId.CROP_PROFILE
    assert selected == list(TreeId)


def test_minimal_context_selects_only_crop_profile(crop_profile):
    from engine.models.domain import AgriculturalContext

    context = AgriculturalContext(
        request_id="minimal-request",
        crop_id="test-crop",
        channel=Channel.MOBILE,
        crop_profile=crop_profile,
    )
    assert CropTreeSelector().select(context) == [TreeId.CROP_PROFILE]


def test_sms_selects_proactive_priority_trees(context):
    context.channel = Channel.SMS
    context.present = {}
    context.past = {}
    context.future = {}
    context.region = "West"
    selected = CropTreeSelector().select(context)
    assert selected == [
        TreeId.CROP_PROFILE,
        TreeId.REGION,
        TreeId.WEATHER,
        TreeId.TIMING,
        TreeId.PRACTICES_RISKS,
    ]


def test_expand_preserves_order_and_root():
    selected = CropTreeSelector().expand([TreeId.SOIL], [TreeId.WEATHER, TreeId.SOIL])
    assert selected == [TreeId.CROP_PROFILE, TreeId.SOIL, TreeId.WEATHER]

