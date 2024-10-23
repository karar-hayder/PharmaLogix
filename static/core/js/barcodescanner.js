const codeReader = new ZXing.BrowserMultiFormatReader();
const videoElement = document.getElementById('video');
const resultElement = document.getElementById('scanned-barcode');
let lastScannedCode = '';

function sendBarcode(code) {
    fetch(`/api/pharmacy/${pharmacyId}/search/?barcode=${encodeURIComponent(code)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.length > 0) {
                const item = data[0];
                if (item && item.id) {
                    addToCart(item.id, 1);
                } else {
                    console.error('Item or item ID is not defined');
                }
            } else {
                console.error('No items found');
            }
        })
        .catch(error => {
            console.error('Error fetching search results:', error);
            resultElement.innerText = 'Error fetching search results';
        });
}

function startScanning() {
    codeReader.decodeFromVideoDevice(null, videoElement, (result, err) => {
        if (result && result.text.length >= 10) {
            if (result.text !== lastScannedCode) {
                lastScannedCode = result.text;
                resultElement.innerText = `Scanned: ${result.text}`;
                audio.play();
                sendBarcode(result.text);
            }
        }
        if (err && !(err instanceof ZXing.NotFoundException)) {
            console.error(err);
        }
    });
}

startScanning();