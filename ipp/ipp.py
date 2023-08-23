from typing import Any
from typing import Mapping
from typing import Optional
from struct import error as StructError
from socket import gaierror as SocketGIAError

import requests
from yarl import URL
from deepmerge import always_merger

from .const import DEFAULT_CHARSET
from .const import DEFAULT_CHARSET_LANGUAGE
from .const import DEFAULT_JOB_ATTRIBUTES
from .const import DEFAULT_PRINTER_ATTRIBUTES
from .const import DEFAULT_PROTO_VERSION
from .enums import IppOperation
from .enums import IppStatus
from .exceptions import IPPConnectionError
from .exceptions import IPPConnectionUpgradeRequired
from .exceptions import IPPError
from .exceptions import IPPParseError
from .exceptions import IPPResponseError
from .exceptions import IPPVersionNotSupportedError
from .models import Printer
from .parser import parse as parse_response
from .parser import parse_html
from .serializer import encode_dict


class IPP:
    """Main class for handling connections with IPP servers."""

    def __init__(
        self,
        host: str,
        base_path: str = "/ipp/print",
        password: str = None,
        port: int = 631,
        request_timeout: int = 8,
        session: requests.Session = None,
        tls: bool = False,
        username: str = None,
        verify_ssl: bool = False,
        user_agent: str = None,
        proxies: dict = None,
    ) -> None:
        """Initialize connection with IPP server."""
        self._session = session
        self._close_session = False

        self.base_path = base_path
        self.host = host
        self.password = password
        self.port = port
        self.request_timeout = request_timeout
        self.tls = tls
        self.username = username
        self.verify_ssl = verify_ssl
        self.user_agent = user_agent
        self.proxies = proxies

        if host.startswith("ipp://") or host.startswith("ipps://"):
            self.printer_uri = host
            printer_uri = URL(host)
            self.host = printer_uri.host
            self.port = printer_uri.port
            self.tls = printer_uri.scheme == "ipps"
            self.base_path = printer_uri.path
        else:
            self.printer_uri = self._build_printer_uri()

        if user_agent is None:
            self.user_agent = "CUPS/2.3.4 (macOS 11.0.1; x86_64) IPP/2.0"

    def _request(
        self,
        uri: str = "",
        data: Optional[Any] = None,
        file: bytes = None,
        params: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """Handle a request to an IPP server."""
        scheme = "https" if self.tls else "http"

        method = "POST"
        url = URL.build(
            scheme=scheme, host=self.host, port=self.port, path=self.base_path
        ).join(URL(uri))

        auth = None
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/ipp",
            "Accept": "application/ipp",
        }

        if self._session is None:
            self._session = requests.Session()
            self._close_session = True

        if isinstance(data, dict):
            data = encode_dict(data)

        # 附加打印文件
        if file:
            headers["Content-Length"] = str(len(data) + len(file))
            data += file

        response = self._session.request(
            method,
            str(url),
            auth=auth,
            data=data,
            params=params,
            headers=headers,
            timeout=self.request_timeout,
            proxies=self.proxies,
        )
        response.raise_for_status()
        return response

    def _build_printer_uri(self) -> str:
        scheme = "ipps" if self.tls else "ipp"

        return URL.build(
            scheme=scheme, host=self.host, port=self.port, path=self.base_path
        ).human_repr()

    def _message(self, operation: IppOperation, msg: dict) -> dict:
        """Build a request message to be sent to the server."""
        base = {
            "version": DEFAULT_PROTO_VERSION,
            "operation": operation,
            "request-id": None,  # will get added by serializer if one isn't given
            "operation-attributes-tag": {  # these are required to be in this order
                "attributes-charset": DEFAULT_CHARSET,
                "attributes-natural-language": DEFAULT_CHARSET_LANGUAGE,
                "printer-uri": self.printer_uri,
                # "requesting-user-name": "PythonIPP",
            },
        }

        if not isinstance(msg, dict):
            msg = {}

        return always_merger.merge(base, msg)

    def execute(self, operation: IppOperation, message: dict, file: bytes = None) -> dict:
        """Send a request message to the server."""
        message = self._message(operation, message)
        response = self._request(data=message, file=file)

        try:
            if response.headers.get("Content-Type", "").find("text/html") != -1:
                parsed = parse_html(response.content)
            else:
                try:
                    parsed = parse_response(response.content)
                except Exception:
                    parsed = parse_response(response.content, force_offset=True)
        except (StructError, Exception) as exc:  # disable=broad-except
            raise IPPParseError from exc

        if parsed["status-code"] == IppStatus.ERROR_VERSION_NOT_SUPPORTED:
            raise IPPVersionNotSupportedError("IPP version not supported by server")

        if parsed["status-code"] not in [
            IppStatus.OK,
            IppStatus.OK_IGNORED_OR_SUBSTITUTED,
        ]:
            raise IPPError(
                "Unexpected printer status code",
                {
                    "status-code": parsed["status-code"],
                    "status-msg": IppStatus(parsed["status-code"]).name,
                },
            )

        return parsed

    def raw(self, operation: IppOperation, message: dict) -> bytes:
        """Send a request message to the server and return raw response."""
        message = self._message(operation, message)

        return self._request(data=message)

    def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            self._session.close()

    def printer(self) -> Printer:
        """Get printer information from server."""
        response_data = self.execute(
            IppOperation.GET_PRINTER_ATTRIBUTES,
            {
                "operation-attributes-tag": {
                    "requested-attributes": DEFAULT_PRINTER_ATTRIBUTES,
                },
            },
        )

        parsed: dict = next(iter(response_data["printers"] or []), {})

        try:
            printer = Printer.from_dict(parsed)
        except Exception as exc:  # disable=broad-except
            raise IPPParseError from exc

        return printer

    def create_job(self, job_name=None, copies=1, priority=50):
        response_data = self.execute(
            IppOperation.CREATE_JOB,
            {
                "operation-attributes-tag": {"job-name": job_name},
                "job_attributes": {"copies": copies, "job-priority": priority},
            },
        )

        parsed: dict = next(iter(response_data["jobs"] or []), {})
        job_id = parsed.get("job-id")
        return job_id

    def print_file(
        self,
        job_id: int,
        file: bytes,
        job_name=None,
        document_format="application/octet-stream",
    ) -> dict:
        """Get printer information from server."""

        response_data = self.execute(
            IppOperation.SEND_DOCUMENT,
            {
                "operation-attributes-tag": {
                    "job-id": job_id,
                    "document-name": job_name,
                    "document-format": document_format,
                    "last-document": True,
                },
            },
            file=file,
        )
        return response_data

    def get_job_attributes(self, job_id: int) -> dict:
        """Get printer information from server."""
        response_data = self.execute(
            IppOperation.GET_JOB_ATTRIBUTES,
            {
                "operation-attributes-tag": {
                    "job-id": job_id,
                    "requested-attributes": DEFAULT_JOB_ATTRIBUTES,
                },
            },
        )

        parsed: dict = next(iter(response_data["jobs"] or []), {})
        return parsed

    def cancel_job(self, job_id: int) -> dict:
        """Get printer information from server."""
        response_data = self.execute(
            IppOperation.CANCEL_JOB,
            {
                "operation-attributes-tag": {
                    "job-id": job_id,
                },
            },
        )
        return response_data

    def __enter__(self) -> "IPP":
        """enter."""
        return self

    def __exit__(self, *exc_info) -> None:
        """exit."""
        self.close()
