// Servidor para WhatsApp Web JS que expone una API REST
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Cargar variables de entorno
dotenv.config();

const ADMIN_NUMBER = process.env.ADMIN_NUMBER;

// Inicializar Express
const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Estado del cliente
let clientReady = false;

// Inicializar el cliente de WhatsApp
console.log('Iniciando cliente de WhatsApp Web...');
const client = new Client({
    authStrategy: new LocalAuth({ clientId: 'whatsapp-bot' }),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// Evento al generar código QR para autenticación
client.on('qr', (qr) => {
    console.log('QR GENERADO. Escanea con WhatsApp en tu teléfono.');
    qrcode.generate(qr, { small: true });
    
    // También guardamos el QR en un archivo para acceder desde el navegador si es necesario
    fs.writeFileSync('last_qr.txt', qr);
});

// Evento cuando el cliente está listo
client.on('ready', () => {
    clientReady = true;
    console.log('Cliente de WhatsApp Web JS listo y conectado!');
});

// Evento cuando se recibe un mensaje
client.on('message', async (message) => {
    try {
        console.log(`Mensaje recibido de ${message.from}: ${message.body}`);
        
        // Si el mensaje incluye medios (como un archivo Excel)
        if (message.hasMedia) {
            const media = await message.downloadMedia();
            
            // Si es un Excel, guardarlo
            if (media.mimetype.includes('spreadsheet') || media.filename?.endsWith('.xlsx')) {
                const buffer = Buffer.from(media.data, 'base64');
                fs.writeFileSync('invitados.xlsx', buffer);
                console.log('Archivo Excel recibido y guardado como invitados.xlsx');
                
                // Hacer una solicitud al backend de Python para procesar el Excel
                fetch('http://localhost:5000/process-excel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ from: message.from.replace('@c.us', '') })
                }).catch(err => console.error('Error al llamar al backend de Python:', err));
            }
        }
        
        // Reenviar el mensaje al backend de Python
        fetch('http://localhost:5000/webhook', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                From: message.from.replace('@c.us', ''),
                Body: message.body,
                HasMedia: message.hasMedia
            })
        }).catch(err => console.error('Error al llamar al backend de Python:', err));
        
    } catch (error) {
        console.error('Error al procesar mensaje:', error);
    }
});

// API REST para enviar mensajes
app.post('/send-message', async (req, res) => {
    try {
        if (!clientReady) {
            return res.status(503).json({ 
                status: 'error', 
                message: 'Cliente de WhatsApp no está listo. Por favor, escanea el código QR.' 
            });
        }
        
        const { number, message } = req.body;
        
        // Formatear número para WhatsApp
        let formattedNumber = number;
        if (!formattedNumber.includes('@c.us')) {
            formattedNumber = `${formattedNumber}@c.us`;
        }
        
        // Enviar mensaje
        await client.sendMessage(formattedNumber, message);
        
        console.log(`Mensaje enviado a ${formattedNumber}: ${message}`);
        res.json({ status: 'success', message: 'Mensaje enviado con éxito' });
    } catch (error) {
        console.error('Error al enviar mensaje:', error);
        res.status(500).json({ status: 'error', message: error.message });
    }
});

// API para enviar archivos
app.post('/send-file', async (req, res) => {
    try {
        if (!clientReady) {
            return res.status(503).json({ 
                status: 'error', 
                message: 'Cliente de WhatsApp no está listo' 
            });
        }
        
        const { number, filePath, caption } = req.body;
        
        // Verificar que el archivo existe
        if (!fs.existsSync(filePath)) {
            return res.status(404).json({ 
                status: 'error', 
                message: `Archivo no encontrado: ${filePath}` 
            });
        }
        
        // Formatear número para WhatsApp
        let formattedNumber = number;
        if (!formattedNumber.includes('@c.us')) {
            formattedNumber = `${formattedNumber}@c.us`;
        }
        
        // Crear media desde archivo
        const media = MessageMedia.fromFilePath(filePath);
        
        // Enviar archivo
        await client.sendMessage(formattedNumber, media, { caption });
        
        console.log(`Archivo enviado a ${formattedNumber}: ${filePath}`);
        res.json({ status: 'success', message: 'Archivo enviado con éxito' });
    } catch (error) {
        console.error('Error al enviar archivo:', error);
        res.status(500).json({ status: 'error', message: error.message });
    }
});

// Endpoint para verificar el estado del cliente
app.get('/status', (req, res) => {
    res.json({
        status: clientReady ? 'ready' : 'not_ready',
        message: clientReady ? 'Cliente WhatsApp conectado' : 'Cliente WhatsApp no conectado'
    });
});

// Iniciar el cliente de WhatsApp
client.initialize();

// Iniciar el servidor Express
const PORT = process.env.WHATSAPP_SERVER_PORT || 3000;
app.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${PORT}`);
    console.log('Esperando a que el cliente de WhatsApp se conecte...');
}); 