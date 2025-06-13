class Validators {
  static String? validateEmail(String value) {
    final emailRegex = RegExp(r"^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$");
    if (value.isEmpty) return 'El correo es obligatorio';
    if (!emailRegex.hasMatch(value)) return 'Correo inválido';
    return null;
  }

  static String? validateCedula(String value) {
    if (value.isEmpty) return 'La cédula es obligatoria';
    if (!RegExp(r'^\d+$').hasMatch(value)) return 'Solo se permiten números';
    return null;
  }


  static String? validatePhoneNumber(String value) {
    if (value.isEmpty) return 'El número es obligatorio';
    if (!RegExp(r'^\d{10}$').hasMatch(value)) return 'Debe tener 10 dígitos';
    return null;
  }

  static String? validateText(String value, String label) {
    if (value.isEmpty) return '$label es obligatorio';
    return null;
  }
}
