from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from crud.imageRepo import create_image, process_image, update_image


# Mock boto3 client
@pytest.fixture
def mock_s3_client():
    with patch("crud.imageRepo.s3") as mock_s3:
        yield mock_s3

# Mock the UploadFile object
@pytest.fixture
def mock_upload_file():
    # Create a simple image in memory
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    # Mock UploadFile with image content
    upload_file = UploadFile(filename="test_image.jpg", file=img_bytes)
    return upload_file

# Test the create_image function
@pytest.mark.asyncio
async def test_create_image(mock_s3_client, mock_upload_file):
    # Mock S3 put_object to not actually upload
    mock_s3_client.put_object.return_value = {}

    # Call the function
    folder = "test_folder"
    result = await create_image(mock_upload_file, folder)

    # Assert that S3's put_object was called with the correct arguments
    mock_s3_client.put_object.assert_called_once()
    assert "https://" in result  # Check if the result is a URL

# Test the update_image function
@pytest.mark.asyncio
@patch("crud.imageRepo.AWS_S3_BUCKET", "mocked_bucket")
async def test_update_image(mock_s3_client, mock_upload_file):
    # Mock the S3 list_objects_v2 and delete_object methods
    mock_s3_client.list_objects_v2.return_value = {'Contents': [{'Key': 'test_folder/old_image.jpg'}]}
    mock_s3_client.delete_object.return_value = {}

    # Mock S3 put_object to not actually upload
    mock_s3_client.put_object.return_value = {}

    # Call the function
    folder = "test_folder"
    result = await update_image(mock_upload_file, folder)

    # Assert that S3's list_objects_v2 and delete_object were called
    mock_s3_client.list_objects_v2.assert_called_once()
    mock_s3_client.delete_object.assert_called_once_with(Bucket="mocked_bucket", Key='test_folder/old_image.jpg')

    # Assert that S3's put_object was called to upload the new image
    mock_s3_client.put_object.assert_called_once()
    assert "https://" in result  # Check if the result is a URL

# Test the process_image function
@pytest.mark.asyncio
async def test_process_image(mock_s3_client, mock_upload_file):
    # Mock S3 put_object to not actually upload
    mock_s3_client.put_object.return_value = {}

    # Call the function
    folder = "test_folder"
    result = await process_image(mock_upload_file, folder)

    # Assert that S3's put_object was called
    mock_s3_client.put_object.assert_called_once()

    # Assert that the returned URL is correct
    assert "https://" in result

# Teste para exceção lançada ao processar uma imagem inválida
@pytest.mark.asyncio
async def test_process_image_invalid_image():
    # Simula um arquivo inválido que não pode ser aberto como imagem
    invalid_file = UploadFile(filename="invalid.txt", file=BytesIO(b"not_an_image"))

    with pytest.raises(HTTPException) as exc_info:
        await process_image(invalid_file, "test_folder")

    # Verifica se o status code da exceção é 400 e a mensagem é 'Invalid image'
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid image"

# Teste para exceção lançada ao usar um formato de imagem não suportado
@pytest.mark.asyncio
async def test_process_image_invalid_format(monkeypatch):
    # Simula uma imagem com formato inválido (não JPEG, PNG, BMP, GIF)
    img_mock = MagicMock()
    img_mock.format = "TIFF"  # Formato não suportado

    def mock_open_image(*args, **kwargs):
        return img_mock

    # Substitui PIL.Image.open para retornar a imagem com formato não suportado
    monkeypatch.setattr("PIL.Image.open", mock_open_image)

    # Cria um UploadFile válido (o formato será definido pelo mock)
    valid_file = UploadFile(filename="test_image.tiff", file=BytesIO(b"valid_image_content"))

    with pytest.raises(HTTPException) as exc_info:
        await process_image(valid_file, "test_folder")

    # Verifica se o status code da exceção é 400 e a mensagem é 'Invalid image format'
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid image format"
