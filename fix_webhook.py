#!/usr/bin/env python
# Script to fix indentation issues in webhook.py

def main():
    print("Fixing webhook.py...")
    try:
        with open('webhook.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix the send_message method indentation issue
        fixed_content = content.replace(
            '''                if response.status_code == 200:
                    print(f"Mensaje enviado a {clean_number} usando WhatsApp Web JS")
                    return True
    else:
                    print(f"Error al enviar mensaje usando WhatsApp Web JS: {response.text}")
                    return False''',
            '''                if response.status_code == 200:
                    print(f"Mensaje enviado a {clean_number} usando WhatsApp Web JS")
                    return True
                else:
                    print(f"Error al enviar mensaje usando WhatsApp Web JS: {response.text}")
                    return False''')

        # Fix the Twilio format parsing indentation issue
        fixed_content = fixed_content.replace(
            '''    else:
        # Formato de Twilio
    data = request.form
    numero = data.get("From", "").replace("whatsapp:", "").replace("+", "")
        mensaje = data.get("Body", "").strip()
        media_url = data.get("MediaUrl0", "")''',
            '''    else:
        # Formato de Twilio
        data = request.form
        numero = data.get("From", "").replace("whatsapp:", "").replace("+", "")
        mensaje = data.get("Body", "").strip()
        media_url = data.get("MediaUrl0", "")''')

        # Fix the success/else indentation issue
        fixed_content = fixed_content.replace(
            '''    if success:
        is_organizador = True
        print(f"- Es organizador: Sí (ID: {organizador['id']})")
        else:
        print(f"- Es organizador: No (verificando si inicia sesión)")''',
            '''    if success:
        is_organizador = True
        print(f"- Es organizador: Sí (ID: {organizador['id']})")
    else:
        print(f"- Es organizador: No (verificando si inicia sesión)")''')

        # Fix the success/else indentation issue for registration results
        fixed_content = fixed_content.replace(
            '''            if success:
                print(f"✅ Organizador registrado automáticamente: {resultado['id']}")
                organizador = resultado
    else:
                print(f"❌ Error al registrar organizador: {resultado}")''',
            '''            if success:
                print(f"✅ Organizador registrado automáticamente: {resultado['id']}")
                organizador = resultado
            else:
                print(f"❌ Error al registrar organizador: {resultado}")''')

        with open('webhook.py', 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print("Indentation issues fixed in webhook.py")
        return True
    except Exception as e:
        print(f"Error fixing webhook.py: {e}")
        return False

if __name__ == "__main__":
    main() 