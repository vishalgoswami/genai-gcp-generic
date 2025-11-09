#!/usr/bin/env python3
"""
Google Cloud DLP (Data Loss Prevention) Scanner
Inspects, deidentifies, and redacts sensitive data in messages
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import google.cloud.dlp_v2


class DLPMode(Enum):
    """DLP processing modes"""
    INSPECT_ONLY = "inspect_only"      # Only detect sensitive data, don't modify
    DEIDENTIFY = "deidentify"          # Replace with tokens/surrogates
    REDACT = "redact"                  # Remove sensitive data completely
    DISABLED = "disabled"              # No DLP processing


class DLPMethod(Enum):
    """Deidentification methods"""
    MASKING = "masking"               # Replace with asterisks (****)
    TOKENIZATION = "tokenization"     # Replace with reversible tokens
    REDACTION = "redaction"           # Complete removal


@dataclass
class DLPResult:
    """Result from DLP scanning"""
    original_text: str
    processed_text: str
    findings: List[Dict[str, Any]]
    mode: DLPMode
    has_sensitive_data: bool
    findings_count: int
    info_types_found: List[str]
    
    @property
    def has_findings(self) -> bool:
        """Alias for has_sensitive_data for compatibility"""
        return self.has_sensitive_data
    
    @property
    def info_type_summary(self) -> str:
        """Get comma-separated summary of info types found"""
        return ", ".join(self.info_types_found) if self.info_types_found else "None"
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if not self.has_sensitive_data:
            return "✅ No sensitive data detected"
        
        summary = [f"⚠️ Found {self.findings_count} sensitive data instance(s):"]
        
        # Group by info type
        info_type_counts = {}
        for finding in self.findings:
            info_type = finding.get('info_type', 'UNKNOWN')
            info_type_counts[info_type] = info_type_counts.get(info_type, 0) + 1
        
        for info_type, count in info_type_counts.items():
            summary.append(f"   • {info_type}: {count} instance(s)")
        
        if self.mode == DLPMode.DEIDENTIFY:
            summary.append("   ℹ️ Sensitive data has been deidentified")
        elif self.mode == DLPMode.REDACT:
            summary.append("   ℹ️ Sensitive data has been redacted")
        
        return "\n".join(summary)


class DLPScanner:
    """Google Cloud DLP scanner for sensitive data detection and protection"""
    
    # Default info types to detect
    DEFAULT_INFO_TYPES = [
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "CREDIT_CARD_NUMBER",
        "US_SOCIAL_SECURITY_NUMBER",
        "IP_ADDRESS",
        "PASSPORT",
        "PERSON_NAME",
        "LOCATION",
        "DATE_OF_BIRTH",
        "AGE",
        "GENDER",
        "US_BANK_ROUTING_MICR",
        "STREET_ADDRESS",
        "US_STATE",
        "URL",
        "MEDICAL_RECORD_NUMBER",
        "US_HEALTHCARE_NPI",
    ]
    
    def __init__(
        self,
        project_id: str,
        mode: DLPMode = DLPMode.INSPECT_ONLY,
        deidentify_method: DLPMethod = DLPMethod.MASKING,
        info_types: Optional[List[str]] = None,
        min_likelihood: str = "POSSIBLE",
        enable_logging: bool = True
    ):
        """
        Initialize DLP scanner
        
        Args:
            project_id: GCP project ID
            mode: DLP processing mode
            deidentify_method: Method for deidentification
            info_types: List of info types to detect (None = use defaults)
            min_likelihood: Minimum likelihood threshold (POSSIBLE, LIKELY, VERY_LIKELY)
            enable_logging: Enable detailed logging
        """
        self.project_id = project_id
        self.mode = mode
        self.deidentify_method = deidentify_method
        self.info_types = info_types or self.DEFAULT_INFO_TYPES
        self.min_likelihood = min_likelihood
        self.enable_logging = enable_logging
        
        # Initialize DLP client
        try:
            self.client = google.cloud.dlp_v2.DlpServiceClient()
            if self.enable_logging:
                print(f"✓ DLP client initialized (mode: {mode.value})")
        except Exception as e:
            if self.enable_logging:
                print(f"⚠️ DLP client initialization failed: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if DLP is available"""
        return self.client is not None
    
    def _create_inspect_config(self) -> Dict[str, Any]:
        """Create inspection configuration"""
        info_types = [{"name": info_type} for info_type in self.info_types]
        
        inspect_config = {
            "info_types": info_types,
            "min_likelihood": self.min_likelihood,
            "include_quote": True,
            "limits": {
                "max_findings_per_request": 0  # No limit
            }
        }
        
        return inspect_config
    
    def inspect_text(self, text: str) -> DLPResult:
        """
        Inspect text for sensitive data
        
        Args:
            text: Text to inspect
            
        Returns:
            DLPResult with findings
        """
        if not self.is_available():
            if self.enable_logging:
                print("⚠️ DLP not available, returning original text")
            return DLPResult(
                original_text=text,
                processed_text=text,
                findings=[],
                mode=DLPMode.DISABLED,
                has_sensitive_data=False,
                findings_count=0,
                info_types_found=[]
            )
        
        try:
            # Create inspection request
            parent = f"projects/{self.project_id}"
            item = {"value": text}
            inspect_config = self._create_inspect_config()
            
            # Call DLP API
            response = self.client.inspect_content(
                request={
                    "parent": parent,
                    "inspect_config": inspect_config,
                    "item": item
                }
            )
            
            # Process findings
            findings = []
            info_types_found = set()
            
            if response.result.findings:
                for finding in response.result.findings:
                    info_type = finding.info_type.name
                    info_types_found.add(info_type)
                    
                    findings.append({
                        "info_type": info_type,
                        "likelihood": finding.likelihood.name,
                        "quote": finding.quote,
                        "location": {
                            "byte_start": finding.location.byte_range.start,
                            "byte_end": finding.location.byte_range.end
                        }
                    })
                    
                    if self.enable_logging:
                        print(f"   Found {info_type}: '{finding.quote}' (likelihood: {finding.likelihood.name})")
            
            return DLPResult(
                original_text=text,
                processed_text=text,  # No modification in inspect mode
                findings=findings,
                mode=DLPMode.INSPECT_ONLY,
                has_sensitive_data=len(findings) > 0,
                findings_count=len(findings),
                info_types_found=sorted(list(info_types_found))
            )
            
        except Exception as e:
            if self.enable_logging:
                print(f"⚠️ DLP inspection failed: {e}")
            return DLPResult(
                original_text=text,
                processed_text=text,
                findings=[],
                mode=DLPMode.DISABLED,
                has_sensitive_data=False,
                findings_count=0,
                info_types_found=[]
            )
    
    def deidentify_text(self, text: str, method: Optional[DLPMethod] = None) -> DLPResult:
        """
        Deidentify sensitive data in text
        
        Args:
            text: Text to deidentify
            method: Deidentification method (None = use instance default)
            
        Returns:
            DLPResult with deidentified text
        """
        if not self.is_available():
            if self.enable_logging:
                print("⚠️ DLP not available, returning original text")
            return DLPResult(
                original_text=text,
                processed_text=text,
                findings=[],
                mode=DLPMode.DISABLED,
                has_sensitive_data=False,
                findings_count=0,
                info_types_found=[]
            )
        
        method = method or self.deidentify_method
        
        try:
            # First inspect to get findings
            inspect_result = self.inspect_text(text)
            
            if not inspect_result.has_sensitive_data:
                # No sensitive data, return as-is
                return DLPResult(
                    original_text=text,
                    processed_text=text,
                    findings=[],
                    mode=DLPMode.DEIDENTIFY,
                    has_sensitive_data=False,
                    findings_count=0,
                    info_types_found=[]
                )
            
            # Create deidentification config based on method
            parent = f"projects/{self.project_id}"
            item = {"value": text}
            inspect_config = self._create_inspect_config()
            
            if method == DLPMethod.MASKING:
                # Replace with asterisks
                deidentify_config = {
                    "info_type_transformations": {
                        "transformations": [
                            {
                                "primitive_transformation": {
                                    "character_mask_config": {
                                        "masking_character": "*",
                                        "number_to_mask": 0  # Mask all characters
                                    }
                                }
                            }
                        ]
                    }
                }
            elif method == DLPMethod.TOKENIZATION:
                # Crypto-based reversible tokenization
                deidentify_config = {
                    "info_type_transformations": {
                        "transformations": [
                            {
                                "primitive_transformation": {
                                    "crypto_replace_ffx_fpe_config": {
                                        "crypto_key": {
                                            "unwrapped": {
                                                "key": b"0123456789abcdef0123456789abcdef"  # 32-byte key
                                            }
                                        },
                                        "common_alphabet": "ALPHA_NUMERIC"
                                    }
                                }
                            }
                        ]
                    }
                }
            else:  # REDACTION
                # Complete removal
                deidentify_config = {
                    "info_type_transformations": {
                        "transformations": [
                            {
                                "primitive_transformation": {
                                    "replace_config": {
                                        "new_value": {"string_value": "[REDACTED]"}
                                    }
                                }
                            }
                        ]
                    }
                }
            
            # Call deidentify API
            response = self.client.deidentify_content(
                request={
                    "parent": parent,
                    "deidentify_config": deidentify_config,
                    "inspect_config": inspect_config,
                    "item": item
                }
            )
            
            deidentified_text = response.item.value
            
            if self.enable_logging:
                print(f"   ✓ Deidentified using {method.value}")
                print(f"   Original: {text[:100]}...")
                print(f"   Deidentified: {deidentified_text[:100]}...")
            
            return DLPResult(
                original_text=text,
                processed_text=deidentified_text,
                findings=inspect_result.findings,
                mode=DLPMode.DEIDENTIFY,
                has_sensitive_data=True,
                findings_count=inspect_result.findings_count,
                info_types_found=inspect_result.info_types_found
            )
            
        except Exception as e:
            if self.enable_logging:
                print(f"⚠️ DLP deidentification failed: {e}")
            return DLPResult(
                original_text=text,
                processed_text=text,
                findings=[],
                mode=DLPMode.DISABLED,
                has_sensitive_data=False,
                findings_count=0,
                info_types_found=[]
            )
    
    def redact_text(self, text: str) -> DLPResult:
        """
        Redact sensitive data from text (complete removal)
        
        Args:
            text: Text to redact
            
        Returns:
            DLPResult with redacted text
        """
        return self.deidentify_text(text, method=DLPMethod.REDACTION)
    
    def process_text(self, text: str) -> DLPResult:
        """
        Process text according to configured mode
        
        Args:
            text: Text to process
            
        Returns:
            DLPResult with processed text
        """
        if self.mode == DLPMode.DISABLED:
            return DLPResult(
                original_text=text,
                processed_text=text,
                findings=[],
                mode=DLPMode.DISABLED,
                has_sensitive_data=False,
                findings_count=0,
                info_types_found=[]
            )
        elif self.mode == DLPMode.INSPECT_ONLY:
            return self.inspect_text(text)
        elif self.mode == DLPMode.DEIDENTIFY:
            return self.deidentify_text(text)
        elif self.mode == DLPMode.REDACT:
            return self.redact_text(text)
        else:
            return self.inspect_text(text)


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    project_id = os.getenv("PROJECT_ID", "vg-pp-001")
    
    print("=" * 70)
    print("DLP SCANNER TEST")
    print("=" * 70)
    
    # Test text with various sensitive data
    test_text = """
    Hi, my name is John Doe and my email is john.doe@example.com.
    You can call me at 555-123-4567 or send mail to 123 Main St, New York, NY.
    My SSN is 123-45-6789 and credit card is 4532-1234-5678-9010.
    """
    
    print(f"\nOriginal Text:\n{test_text}\n")
    
    # Test 1: Inspect only
    print("\n" + "=" * 70)
    print("TEST 1: INSPECT ONLY")
    print("=" * 70)
    scanner = DLPScanner(project_id, mode=DLPMode.INSPECT_ONLY)
    result = scanner.process_text(test_text)
    print(result.get_summary())
    
    # Test 2: Deidentify with masking
    print("\n" + "=" * 70)
    print("TEST 2: DEIDENTIFY (Masking)")
    print("=" * 70)
    scanner = DLPScanner(project_id, mode=DLPMode.DEIDENTIFY, deidentify_method=DLPMethod.MASKING)
    result = scanner.process_text(test_text)
    print(result.get_summary())
    print(f"\nProcessed Text:\n{result.processed_text}\n")
    
    # Test 3: Redact
    print("\n" + "=" * 70)
    print("TEST 3: REDACT")
    print("=" * 70)
    scanner = DLPScanner(project_id, mode=DLPMode.REDACT)
    result = scanner.process_text(test_text)
    print(result.get_summary())
    print(f"\nProcessed Text:\n{result.processed_text}\n")
