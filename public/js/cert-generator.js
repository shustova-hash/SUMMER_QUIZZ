function generateCertificate(childName, branchName, ticketNumber) {
    const canvas = document.createElement('canvas');
    canvas.width = 1600;
    canvas.height = 1131; // A4 aspect ratio in pixels
    const ctx = canvas.getContext('2d');

    // Background gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 1600, 1131);
    bgGrad.addColorStop(0, '#0a1128');
    bgGrad.addColorStop(0.5, '#001f54');
    bgGrad.addColorStop(1, '#034078');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 1600, 1131);

    // Decorative Borders
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 10;
    ctx.strokeRect(40, 40, 1520, 1051);

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 2;
    ctx.strokeRect(55, 55, 1490, 1021);

    // Corner Ornaments
    ctx.fillStyle = '#00f2fe';
    ctx.fillRect(30, 30, 30, 30);
    ctx.fillRect(1540, 30, 30, 30);
    ctx.fillRect(30, 1071, 30, 30);
    ctx.fillRect(1540, 1071, 30, 30);

    // Academy Title Header
    ctx.font = 'bold 36px "Inter", sans-serif';
    ctx.fillStyle = '#00f2fe';
    ctx.textAlign = 'center';
    ctx.fillText('КОМП\'ЮТЕРНА АКАДЕМІЯ ITSTEP', 800, 160);

    ctx.font = '500 24px "Inter", sans-serif';
    ctx.fillStyle = '#a0aec0';
    ctx.fillText(branchName || 'Філія ITSTEP', 800, 205);

    // Certificate Main Title
    ctx.font = '900 64px "Inter", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.fillText('СЕРТИФІКАТ', 800, 320);

    ctx.font = '500 26px "Inter", sans-serif';
    ctx.fillStyle = '#cbd5e0';
    ctx.fillText('Цей сертифікат засвідчує, що', 800, 390);

    // Child Name Highlighted
    ctx.font = 'bold 56px "Inter", sans-serif';
    const nameGrad = ctx.createLinearGradient(400, 0, 1200, 0);
    nameGrad.addColorStop(0, '#00f2fe');
    nameGrad.addColorStop(1, '#4facfe');
    ctx.fillStyle = nameGrad;
    ctx.fillText(childName || 'Учасник Квізу', 800, 480);

    // Line under name
    ctx.beginPath();
    ctx.moveTo(500, 505);
    ctx.lineTo(1100, 505);
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Achievement text
    ctx.font = '500 28px "Inter", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.fillText('успішно пройшов(ла) інтерактивний IT-квіст', 800, 570);

    ctx.font = 'bold 38px "Inter", sans-serif';
    ctx.fillStyle = '#ffb703';
    ctx.fillText('«Мої літні канікули — це баг чи фіча?»', 800, 635);

    ctx.font = '500 24px "Inter", sans-serif';
    ctx.fillStyle = '#cbd5e0';
    ctx.fillText('та отримав(ла) офіційне підтвердження високого IT-потенціалу!', 800, 690);

    // Raffle Ticket Info
    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.roundRect ? ctx.roundRect(450, 750, 700, 110, 15) : ctx.fillRect(450, 750, 700, 110);
    ctx.fill();
    ctx.strokeStyle = '#ffb703';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.font = 'bold 22px "Inter", sans-serif';
    ctx.fillStyle = '#ffb703';
    ctx.fillText('УНІКАЛЬНИЙ НОМЕР УЧАСНИКА РОЗІГРАШУ ПРИЗІВ:', 800, 790);

    ctx.font = 'bold 36px "Courier New", monospace';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(ticketNumber || 'ITS-000000', 800, 835);

    // Footer info
    const today = new Date().toLocaleDateString('uk-UA', { year: 'numeric', month: 'long', day: 'numeric' });
    ctx.font = '500 20px "Inter", sans-serif';
    ctx.fillStyle = '#a0aec0';
    ctx.textAlign = 'left';
    ctx.fillText(`Дата видачі: ${today}`, 120, 990);

    ctx.textAlign = 'right';
    ctx.fillText('Академія ITSTEP © 2026', 1480, 990);

    // Trigger download
    const link = document.createElement('a');
    link.download = `Certificate_${childName.replace(/\s+/g, '_')}_ITSTEP.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
}
