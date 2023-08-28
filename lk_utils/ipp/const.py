"""Constants for IPP."""

DEFAULT_CHARSET = "utf-8"
DEFAULT_CHARSET_LANGUAGE = "zh-cn"

DEFAULT_CLASS_ATTRIBUTES = ["printer-name", "member-names"]

DEFAULT_JOB_ATTRIBUTES = [
    "job-id",
    "job-name",
    "printer-uri",
    "job-state",
    "job-state-reasons",
    "job-hold-until",
    "job-media-progress",
    "job-k-octets",
    "number-of-documents",
    "copies",
    "job-originating-user-name",
]

DEFAULT_PRINTER_ATTRIBUTES = [
    "printer-uuid",
    "printer-up-time",
    "printer-device-id",
    "printer-name",
    "printer-type",
    "printer-location",
    "printer-info",
    "printer-make-and-model",
    "printer-state",
    "printer-state-message",
    "printer-state-reasons",
    "printer-uri-supported",
    "uri-authentication-supported",
    "uri-security-supported",
    "device-uri",
    "printer-firmware-string-version",
    "printer-is-shared",
    "marker-names",
    "marker-colors",
    "marker-levels",
    "marker-high-levels",
    "marker-low-levels",
    "marker-types",
]

DEFAULT_PORT = 631
DEFAULT_PROTO_VERSION = (2, 0)
