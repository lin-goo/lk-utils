import requests
import xmltodict

# To be edited...
ALLOW_MAX_A4_SIZE = False


class ESCLScanner:
    a4_width_px_300dpi = 2480
    a4_height_px_300dpi = 3508

    # These are scanner dependent values...
    format_to_mime = {
        "PDF": "application/pdf",
        "JPEG": "image/jpeg",
        "PRN": "application/octet-stream",
        "tiff": "image/tiff",
    }
    name_to_color_modes = {
        "BackAndWhite": "BlackAndWhite1",
        "Grayscale": "Grayscale8",
        "Color": "RGB24",
        "SuperColor": "RGB48",
    }
    mime_to_format = {v: k for k, v in format_to_mime.items()}
    color_modes_to_name = {v: k for k, v in name_to_color_modes.items()}

    query_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <scan:ScanSettings xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm"
                       xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03">
      <pwg:Version>{0}</pwg:Version>
      <pwg:ScanRegions pwg:MustHonor="true">
        <pwg:ScanRegion>
          <pwg:ContentRegionUnits>escl:ThreeHundredthsOfInches</pwg:ContentRegionUnits>
          <pwg:Height>{1}</pwg:Height>
          <pwg:Width>{2}</pwg:Width>
          <pwg:XOffset>0</pwg:XOffset>
          <pwg:YOffset>0</pwg:YOffset>
        </pwg:ScanRegion>
      </pwg:ScanRegions>
      <pwg:InputSource>{3}</pwg:InputSource>
      <scan:ColorMode>{4}</scan:ColorMode>
      <scan:XResolution>{5}</scan:XResolution>
      <scan:YResolution>{5}</scan:YResolution>
      <pwg:DocumentFormat>{6}</pwg:DocumentFormat>
      <scan:Intent>{7}</scan:Intent>
    </scan:ScanSettings>"""

    def __init__(self, target_ip, port, proxies=None, timeout=10):
        self.proxies = proxies
        self.timeout = timeout
        self.scanner_ip = f"{target_ip}:{port}"

    def _get_from_url(self, url):
        resp = requests.get(url, timeout=self.timeout, proxies=self.proxies)
        resp.raise_for_status()
        return resp.content

    def _get_range(self, inp_caps):
        """
        A4 (210mm x 297mm) 2480px x 3508px @300DPI
        The latter format is returned. Must compute other sizes for other DPIs!
        """
        min_width = int(inp_caps["scan:MinWidth"])
        max_width = int(inp_caps["scan:MaxWidth"])
        min_height = int(inp_caps["scan:MinHeight"])
        max_height = int(inp_caps["scan:MaxHeight"])

        if ALLOW_MAX_A4_SIZE:
            max_width = min(max_width, self.a4_width_px_300dpi)
            max_height = min(max_height, self.a4_height_px_300dpi)

        width_range = range(min_width, max_width + 1)
        height_range = range(min_height, max_height + 1)
        return width_range, height_range

    @staticmethod
    def get_item_by_ordered_dict(item):
        if type(item) == str:
            return item
        else:
            return item["#text"]

    def _get_resolutions(self, inp_caps):
        discrete_resolutions = inp_caps["scan:SettingProfiles"]["scan:SettingProfile"][
            "scan:SupportedResolutions"
        ]["scan:DiscreteResolutions"]["scan:DiscreteResolution"]
        x_resolutions = []
        y_resolutions = []
        if isinstance(discrete_resolutions, list):
            for discrete_resolution in discrete_resolutions:
                x_resolutions.append(
                    int(
                        self.get_item_by_ordered_dict(
                            discrete_resolution["scan:XResolution"]
                        )
                    )
                )
                y_resolutions.append(
                    int(
                        self.get_item_by_ordered_dict(
                            discrete_resolution["scan:YResolution"]
                        )
                    )
                )
                # x_resolutions = [int(text) for text in discrete_resolution["scan:XResolution"]]
                # y_resolutions = [int(text) for text in discrete_resolution["scan:YResolution"]]
        else:
            x_resolutions.append(
                int(
                    self.get_item_by_ordered_dict(
                        discrete_resolutions["scan:XResolution"]
                    )
                )
            )
            y_resolutions.append(
                int(
                    self.get_item_by_ordered_dict(
                        discrete_resolutions["scan:YResolution"]
                    )
                )
            )
        return sorted(
            (min(x, y) for x, y in zip(x_resolutions, y_resolutions)), reverse=True
        )

    @staticmethod
    def _get_max_optical_resolution(inp_caps):
        x_max_optical_resolution = 0
        y_max_optical_resolution = 0
        if inp_caps.get("scan:MaxOpticalXResolution"):
            x_max_optical_resolution = int(inp_caps["scan:MaxOpticalXResolution"])
        if inp_caps.get("scan:MaxOpticalYResolution"):
            y_max_optical_resolution = int(inp_caps["scan:MaxOpticalYResolution"])
        return min(x_max_optical_resolution, y_max_optical_resolution)

    def get_capabilities(self):
        scanner_status_xml = self._get_from_url(
            "http://{0}/eSCL/ScannerStatus".format(self.scanner_ip)
        )
        scanner_status_xml = xmltodict.parse(scanner_status_xml)
        status = scanner_status_xml["scan:ScannerStatus"]["pwg:State"]

        scanner_cap_xml = self._get_from_url(
            "http://{0}/eSCL/ScannerCapabilities".format(self.scanner_ip)
        )
        scanner_cap_xml = xmltodict.parse(scanner_cap_xml)
        scanner_capabilities = scanner_cap_xml["scan:ScannerCapabilities"]
        escl_version = scanner_capabilities["pwg:Version"]
        make_and_model = scanner_capabilities["pwg:MakeAndModel"]
        serial_number = scanner_capabilities["pwg:SerialNumber"]

        caps = {}
        for source_name1, source_name2, source_name3 in (
            ("Platen", "Platen", "Platen"),
            ("Adf", "AdfSimplex", "Feeder"),
        ):
            if not scanner_capabilities.get(f"scan:{source_name1}"):
                continue
            inp_caps = scanner_capabilities[f"scan:{source_name1}"][
                f"scan:{source_name2}InputCaps"
            ]

            width_range, height_range = self._get_range(inp_caps)

            formats = [
                self.mime_to_format[text]
                for text in inp_caps["scan:SettingProfiles"]["scan:SettingProfile"][
                    "scan:DocumentFormats"
                ]["pwg:DocumentFormat"]
            ]

            color_modes = []
            for text in inp_caps["scan:SettingProfiles"]["scan:SettingProfile"][
                "scan:ColorModes"
            ]["scan:ColorMode"]:
                color_modes.append(
                    self.color_modes_to_name[self.get_item_by_ordered_dict(text)]
                )

            color_modes = sorted(color_modes, reverse=True)

            resolutions = self._get_resolutions(inp_caps)

            # Comnpute pixel ranges for different DPIs (must be supplied in 300DPI to the scanner!)
            width_ranges = {}
            height_ranges = {}
            for res in resolutions:
                width_ranges[res] = [
                    width_range.start,
                    (width_range.stop - 1) * res // 300 + 1,
                ]
                height_ranges[res] = [
                    height_range.start,
                    (height_range.stop - 1) * res // 300 + 1,
                ]

            supported_intents = []
            if inp_caps.get("scan:SupportedIntents"):
                for text in inp_caps["scan:SupportedIntents"].get("scan:Intent", []):
                    supported_intents.append(text)
                for text in inp_caps["scan:SupportedIntents"].get(
                    "scan:SupportedIntent", []
                ):
                    supported_intents.append(text)

            max_optical_resolution = self._get_max_optical_resolution(inp_caps)

            caps[source_name3] = {
                "width": width_ranges,
                "height": height_ranges,
                "formats": formats,
                "color_modes": color_modes,
                "resolutions": resolutions,
                "intents": supported_intents,
                "max_optical_resolution": max_optical_resolution,
            }

        return status, {
            "version": escl_version,
            "make_and_model": make_and_model,
            "serial_number": serial_number,
            "caps_by_source": caps,
        }

    def _put_together_query(
        self,
        caps,
        input_source,
        height,
        width,
        color_mode,
        resolution,
        image_format,
        intent,
    ):
        version = caps["version"]
        if input_source not in caps["caps_by_source"]:
            raise ValueError(
                "Input source ({0}) is not in the available input sources ({1})!".format(
                    input_source, caps["caps_by_source"]
                )
            )

        caps_for_curr_source = caps["caps_by_source"][input_source]

        # if height is None:
        #     height = caps_for_curr_source['height'].get(resolution, 300).stop - 1
        # if width is None:
        #     width = caps_for_curr_source['width'].get(resolution, 300).stop - 1

        checks = [
            (resolution, caps_for_curr_source["resolutions"], "Resoluton", "resolutons"),
            (
                height,
                range(
                    caps_for_curr_source["height"][resolution][0],
                    caps_for_curr_source["height"][resolution][1],
                ),
                "Height",
                "range",
            ),
            (
                width,
                range(
                    caps_for_curr_source["width"][resolution][0],
                    caps_for_curr_source["width"][resolution][1],
                ),
                "Width",
                "range",
            ),
            (color_mode, self.name_to_color_modes.keys(), "Color mode", "modes"),
            (image_format, self.format_to_mime.keys(), "Format", "formats"),
            (intent, caps_for_curr_source["intents"], "Intent", "intents"),
        ]
        for value, good_values, name, name_of_values in checks:
            if value not in good_values:
                raise ValueError(
                    "{0} ({1}) is not in {2} ({3})!".format(
                        name, value, name_of_values, good_values
                    )
                )

        # Scale the height and width to 300DPI for the XML
        height = height * 300 // resolution
        width = width * 300 // resolution

        return self.query_xml.format(
            version,
            height,
            width,
            input_source,
            self.name_to_color_modes[color_mode],
            resolution,
            self.format_to_mime[image_format],
            intent,
        )

    def scan(
        self,
        caps,
        input_source,
        height,
        width,
        color_mode,
        resolution,
        image_format,
        intent,
    ):
        try:
            xml = self._put_together_query(
                caps,
                input_source,
                height,
                width,
                color_mode,
                resolution,
                image_format,
                intent,
            )
        except ValueError as msg:
            return msg, 400
        resp = requests.post(
            "http://{0}/eSCL/ScanJobs".format(self.scanner_ip),
            data=xml,
            proxies=self.proxies,
            headers={"Content-Type": "text/xml"},
        )
        if resp.status_code == 201:
            return "{0}/NextDocument".format(resp.headers["Location"]), 201
        return resp.reason, resp.status_code
