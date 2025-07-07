PATIENT_CONFIRMATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; margin: 20px auto; border: 1px solid #dddddd;">
        <!-- ... header part of email ... -->
        <tr>
            <td align="center" bgcolor="#ffffff" style="padding: 40px 0 30px 0;">
                <h1 style="color: #333333; margin-top: 20px;">Your Appointment is Confirmed!</h1>
            </td>
        </tr>
        <tr>
            <td bgcolor="#ffffff" style="padding: 40px 30px 40px 30px;">
                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <!-- ... intro and details table ... -->
                    <tr>
                        <td style="color: #333333; font-size: 16px;">
                            <p>Dear {patient_name},</p>
                            <p>This email confirms your upcoming appointment with us. Please find the details below:</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 0;">
                            <table border="0" cellpadding="10" cellspacing="0" width="100%" style="border: 1px solid #dddddd;">
                                <tr style="background-color: #f9f9f9;">
                                    <td width="150" style="font-weight: bold;">Service:</td>
                                    <td>{service_type}</td>
                                </tr>
                                <tr>
                                    <td style="font-weight: bold;">Date:</td>
                                    <td>{formatted_date}</td>
                                </tr>
                                <tr style="background-color: #f9f9f9;">
                                    <td style="font-weight: bold;">Time:</td>
                                    <td>{formatted_time} (Duration: {duration_minutes} mins)</td>
                                </tr>
                                <tr>
                                    <td style="font-weight: bold;">With:</td>
                                    <td>{doctor_name}</td>
                                </tr>
                                <tr style="background-color: #f9f9f9;">
                                    <td style="font-weight: bold;">Location:</td>
                                    <td>{clinic_address}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 20px 0;">
                            <a href="{patient_add_to_calendar_link}" style="background-color: #4CAF50; color: white; padding: 12px 25px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; font-size: 16px;">Add to Your Calendar</a>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <p>If you need to cancel, please contact us at least 24 hours in advance.</p>
                            <p>We look forward to seeing you!</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

DOCTOR_NOTIFICATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Appointment Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; margin: 20px auto; border: 1px solid #dddddd;">
        <tr>
            <td align="center" bgcolor="#4C78AF" style="padding: 30px 0; color: #ffffff;">
                <h1 style="margin: 0;">New Appointment Booked</h1>
            </td>
        </tr>
        <tr>
            <td bgcolor="#ffffff" style="padding: 40px 30px 40px 30px;">
                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td style="color: #333333; font-size: 16px;">
                            <p>Hello {doctor_name},</p>
                            <p>A new appointment has been booked on your calendar via the AI assistant:</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 0;">
                            <table border="0" cellpadding="10" cellspacing="0" width="100%" style="border: 1px solid #dddddd;">
                                <tr style="background-color: #f9f9f9;">
                                    <td width="150" style="font-weight: bold;">Patient:</td>
                                    <td>{patient_name} (<a href="mailto:{patient_email}">{patient_email}</a>)</td>
                                </tr>
                                <tr>
                                    <td style="font-weight: bold;">Service:</td>
                                    <td>{service_type}</td>
                                </tr>
                                <tr style="background-color: #f9f9f9;">
                                    <td style="font-weight: bold;">When:</td>
                                    <td>{formatted_date} at {formatted_time}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 20px 0;">
                            <a href="{google_event_link}" style="background-color: #007bff; color: white; padding: 12px 25px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; font-size: 16px;">View Event in Google Calendar</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

CANCELLATION_CONFIRMATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Appointment Cancellation</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; margin: 20px auto; border: 1px solid #dddddd; background-color: #ffffff;">
        <tr>
            <td align="center" bgcolor="#dc3545" style="padding: 30px 0; color: #ffffff;">
                <h1 style="margin: 0;">Appointment Canceled</h1>
            </td>
        </tr>
        <tr>
            <td style="padding: 40px 30px;">
                <p style="font-size: 16px;">Dear {patient_name},</p>
                <p style="font-size: 16px;">This email confirms that your appointment has been successfully canceled as requested. The details are below:</p>
                <table border="0" cellpadding="10" cellspacing="0" width="100%" style="border: 1px solid #dddddd; margin-top: 20px;">
                    <tr style="background-color: #f9f9f9;">
                        <td width="150" style="font-weight: bold;">Service:</td>
                        <td>{service_type}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Date:</td>
                        <td>{formatted_date}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="font-weight: bold;">Time:</td>
                        <td>{formatted_time}</td>
                    </tr>
                </table>
                <p style="font-size: 16px; margin-top: 30px;">If you wish to book a new appointment in the future, please don't hesitate to use our AI assistant or contact us directly.</p>
                <p style="font-size: 16px;">Best regards</p>
            </td>
        </tr>
    </table>
</body>
</html>
"""