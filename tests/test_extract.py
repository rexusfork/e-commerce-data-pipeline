
import pandas as pd
import pytest

from ecommerce_pipeline.extract import extract_data


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a temporary Excel dataset."""

    data = {
        "InvoiceNo": ["536365", "536366"],
        "StockCode": ["85123A", "71053"],
        "Description": ["Product A", "Product B"],
        "Quantity": [6, 3],
        "InvoiceDate": [
            "2010-12-01 08:26:00",
            "2010-12-01 08:27:00",
        ],
        "UnitPrice": [2.55, 3.39],
        "CustomerID": [17850, 17850],
        "Country": ["United Kingdom", "United Kingdom"],
    }

    df = pd.DataFrame(data)

    file_path = tmp_path / "sample.xlsx"
    df.to_excel(file_path, index=False)

    return file_path


def test_extract_success(sample_dataset):
    """Extraction should return expected records."""

    df = extract_data(sample_dataset)

    assert len(df) == 2
    assert len(df.columns) == 8
    assert df.iloc[0]["InvoiceNo"] == "536365"


def test_extract_file_not_found(tmp_path):
    """Missing dataset should raise FileNotFoundError."""

    missing_file = tmp_path / "missing.xlsx"

    with pytest.raises(FileNotFoundError):
        extract_data(missing_file)


def test_extract_empty_dataset(tmp_path):
    """Empty dataset should raise ValueError."""

    file_path = tmp_path / "empty.xlsx"

    pd.DataFrame().to_excel(file_path, index=False)

    with pytest.raises(ValueError, match="empty"):
        extract_data(file_path)


def test_extract_missing_columns(tmp_path):
    """Invalid schema should raise ValueError."""

    file_path = tmp_path / "invalid.xlsx"

    pd.DataFrame({
        "InvoiceNo": ["536365"],
        "Quantity": [5],
    }).to_excel(file_path, index=False)

    with pytest.raises(ValueError, match="Missing columns"):
        extract_data(file_path)


def test_extract_preserves_duplicate_invoice(sample_dataset):
    """Multiple line items may share the same invoice."""

    df = pd.read_excel(sample_dataset)
    df.loc[1, "InvoiceNo"] = df.loc[0, "InvoiceNo"]
    df.to_excel(sample_dataset, index=False)

    result = extract_data(sample_dataset)

    assert len(result) == 2
    assert result["InvoiceNo"].nunique() == 1
