import csv
import json
import yaml
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Writer(ABC):
    """Abstract base class for writing data to files."""

    @abstractmethod
    def write(self, data: List[Dict[str, Any]], filename: str) -> None:
        """
        Write a list of dictionaries to the specified file.

        :param data: List of dicts representing the data to write.
        :param filename: The target filename.
        """
        ...


class JsonWriter(Writer):
    """Concrete writer for saving data in JSON format."""

    def write(self, data: List[Dict[str, Any]], filename: str) -> None:
        """
        Write data to a JSON file.

        :param data: List of dicts representing the data to write.
        :param filename: The target filename.
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class CsvWriter(Writer):
    """Concrete writer for saving data in CSV format."""

    def write(self, data: List[Dict[str, Any]], filename: str) -> None:
        """
        Write data to a CSV file.

        :param data: List of dicts representing the data to write.
        :param filename: The target filename.
        :raises RuntimeError: If there is no data to write.
        """
        if not data:
            raise RuntimeError("No data available to write.")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


class YamlWriter(Writer):
    """Concrete writer for saving data in YAML format."""

    def write(self, data: List[Dict[str, Any]], filename: str) -> None:
        """
        Write data to a YAML file.

        :param data: List of dicts representing the data to write.
        :param filename: The target filename.
        :raises RuntimeError: If there is no data to write.
        """
        if not data:
            raise RuntimeError("No data available to write.")
        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )
