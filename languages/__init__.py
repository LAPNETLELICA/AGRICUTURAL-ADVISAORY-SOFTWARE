"""Compatibility exports for legacy channel formatter imports.

The formatter implementation lives in :mod:`integrations.presentation`.
"""

from integrations.presentation import MobileFormatter, SMSFormatter, VoiceFormatter

__all__ = ("MobileFormatter", "SMSFormatter", "VoiceFormatter")
