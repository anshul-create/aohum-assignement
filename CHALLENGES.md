### Challenge C — OTP Resend & Security

OTP handling is designed to prevent reuse and abuse. Each OTP is securely hashed and expires after a fixed TTL, while failed verification attempts are limited. Resending an OTP invalidates the previous OTP and is protected by a cooldown period. Plaintext OTPs are never returned in API responses.


<img width="1377" height="669" alt="Screenshot 2026-08-28 193726" src="https://github.com/user-attachments/assets/4dcea1ef-e3f9-42a1-93d5-cb7a0baf59a6" />
<img width="881" height="374" alt="Screenshot 2026-08-28 195848" src="https://github.com/user-attachments/assets/101ea0aa-89a5-4bc3-8833-99af1309a1d0" />
<img width="995" height="659" alt="Screenshot 2026-08-28 200123" src="https://github.com/user-attachments/assets/87ee6d4e-7289-4af8-b86e-4ef8268a03c9" />

### Challenge B — Cancellation & Re-enrollment

The enrollment lifecycle supports cancellation and re-enrollment without creating duplicate active enrollments. Canceled enrollments are retained for history, while a database constraint ensures that each seeker can have at most one active enrollment for a given event.

<img width="1052" height="799" alt="Screenshot 2026-08-28 173347" src="https://github.com/user-attachments/assets/773d5505-9c1f-41b0-97a4-7e4a3e4a4a8a" />
<img width="1143" height="972" alt="Screenshot 2026-08-28 173713" src="https://github.com/user-attachments/assets/35aa4055-1c00-476c-a40f-8a359c12826a" />
<img width="1358" height="922" alt="Screenshot 2026-08-28 175405" src="https://github.com/user-attachments/assets/b75a2aac-225e-46d9-baf1-1d31c43c7cab" />
<img width="1388" height="644" alt="Screenshot 2026-08-28 180221" src="https://github.com/user-attachments/assets/c03c1133-b438-4daf-bc21-5da7bb8600bd" />
<img width="587" height="230" alt="Screenshot 2026-08-28 191421" src="https://github.com/user-attachments/assets/f6d39ca0-4b6f-4789-b7d6-999f51a621a2" />
<img width="495" height="179" alt="Screenshot 2026-08-28 191655" src="https://github.com/user-attachments/assets/b4ffd04c-2ed6-4e8f-9bc4-075756de3cbc" />
<img width="966" height="362" alt="Screenshot 2026-08-28 192751" src="https://github.com/user-attachments/assets/fcfde1e6-823b-4fd8-b764-a00a8658c47f" />
<img width="995" height="652" alt="Screenshot 2026-08-28 193507" src="https://github.com/user-attachments/assets/27e4b5d2-b465-456c-a3af-156aa7985e31" />
<img width="984" height="645" alt="Screenshot 2026-08-28 193517" src="https://github.com/user-attachments/assets/2bfb4cd0-4b8a-49de-9373-0f390d652727" />
<img width="981" height="647" alt="Screenshot 2026-08-28 193528" src="https://github.com/user-attachments/assets/e3a33476-16b2-4156-867b-ca497ad51be0" />
<img width="960" height="256" alt="Screenshot 2026-08-28 193535" src="https://github.com/user-attachments/assets/3d2c367a-3d4f-4147-9c9a-5a2beefedf4e" />









