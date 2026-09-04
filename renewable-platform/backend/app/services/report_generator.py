"""
Report Generator Service (Module 13 & Section 22).

Generates professional PDF and Excel reports for site assessments and project deployment summaries.
"""
import io
import csv


def generate_site_pdf_report(site_data: dict) -> bytes:
    """Generates a PDF feasibility report for a site."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0F9D58'), spaceAfter=12
        )
        sub_style = ParagraphStyle(
            'DocSub', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1A202C'), spaceAfter=8
        )

        site = site_data.get('site', {})
        env = site_data.get('environmental', {})
        solar = site_data.get('solar', {})
        wind = site_data.get('wind', {})
        score = site_data.get('score', {})
        forecast = site_data.get('forecast', {})

        story.append(Paragraph(f"Site Intelligence Assessment Report", title_style))
        story.append(Paragraph(f"Site Name: <b>{site.get('name', 'N/A')}</b> (Project #{site.get('project_id')})", styles['Normal']))
        story.append(Paragraph(f"Coordinates: {site.get('latitude', 0):.4f}°N, {site.get('longitude', 0):.4f}°E | Region: {site.get('region', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 14))

        # Overall Score Summary Table
        summary_table_data = [
            ['Overall Score', 'Suitability Category', 'Recommended Tech', 'Payback Period'],
            [
                f"{score.get('overall_score', 0):.1f} / 100",
                str(score.get('category', 'N/A')),
                str(score.get('recommended_technology', 'N/A')).upper(),
                f"{forecast.get('payback_period_years', 'N/A')} yrs" if forecast.get('payback_period_years') else 'N/A'
            ]
        ]
        t = Table(summary_table_data, colWidths=[120, 150, 140, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2D3748')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#EDF2F7')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

        # Detailed Physics & Predictions
        story.append(Paragraph("Solar & Wind Potential Breakdown", sub_style))
        details_data = [
            ['Metric', 'Solar Potential', 'Wind Potential'],
            ['Avg Resource Input', f"{env.get('solar_irradiance_kwh_m2_day', 'N/A')} kWh/m²/day", f"{env.get('wind_speed_avg_ms', 'N/A')} m/s"],
            ['Efficiency / Density', f"Eff: {solar.get('panel_efficiency_pct', 'N/A')}%", f"Density: {wind.get('wind_power_density_w_m2', 'N/A')} W/m²"],
            ['Capacity Factor', f"{solar.get('capacity_factor_pct', 'N/A')}%", f"{wind.get('capacity_factor_pct', 'N/A')}%"],
            ['Expected Output (Year 1)', f"{solar.get('expected_energy_output_mwh_year', 'N/A')} MWh", f"{wind.get('expected_annual_energy_mwh', 'N/A')} MWh"],
        ]
        t2 = Table(details_data, colWidths=[160, 185, 185])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A5568')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ]))
        story.append(t2)
        story.append(Spacer(1, 16))

        # Financial & Generation Forecast Table
        story.append(Paragraph("25-Year Generation & Investment Forecast", sub_style))
        fin_data = [
            ['Year 1 Output', 'Year 5 Output', 'Year 10 Output', 'Year 25 Output', 'Est. CAPEX', 'Est. Revenue/Yr'],
            [
                f"{forecast.get('year1_mwh', 0):,.0f} MWh",
                f"{forecast.get('year5_mwh', 0):,.0f} MWh",
                f"{forecast.get('year10_mwh', 0):,.0f} MWh",
                f"{forecast.get('year25_mwh', 0):,.0f} MWh",
                f"${forecast.get('estimated_capex_usd', 0):,.0f}",
                f"${forecast.get('estimated_annual_revenue_usd', 0):,.0f}"
            ]
        ]
        t3 = Table(fin_data, colWidths=[85, 85, 85, 85, 95, 95])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ]))
        story.append(t3)

        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        # Fallback text format
        buf = io.StringIO()
        buf.write(f"SOLAR & WIND DEPLOYMENT INTELLIGENCE PLATFORM REPORT\n")
        buf.write(f"Site: {site_data.get('site', {}).get('name')}\n")
        buf.write(f"Detail: {site_data}\n")
        return buf.getvalue().encode('utf-8')


def generate_site_excel_report(site_data: dict) -> bytes:
    """Generates an Excel workbook for site intelligence evaluation."""
    try:
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Site Evaluation"

        site = site_data.get('site', {})
        env = site_data.get('environmental', {})
        solar = site_data.get('solar', {})
        wind = site_data.get('wind', {})
        score = site_data.get('score', {})
        forecast = site_data.get('forecast', {})

        ws.append(["SOLAR & WIND DEPLOYMENT INTELLIGENCE PLATFORM - SITE REPORT"])
        ws.append([])
        ws.append(["Site Name", site.get("name")])
        ws.append(["Latitude", site.get("latitude")])
        ws.append(["Longitude", site.get("longitude")])
        ws.append(["Region", site.get("region")])
        ws.append(["Land Area (ha)", site.get("land_area_hectares")])
        ws.append(["Elevation (m)", site.get("elevation_m")])
        ws.append([])
        ws.append(["SUITABILITY ASSESSMENT"])
        ws.append(["Overall Score", score.get("overall_score")])
        ws.append(["Category", score.get("category")])
        ws.append(["Recommended Technology", score.get("recommended_technology")])
        ws.append(["Resource Score", score.get("resource_score")])
        ws.append(["Geographic Score", score.get("geographic_score")])
        ws.append(["Infrastructure Score", score.get("infrastructure_score")])
        ws.append(["Environmental Score", score.get("environmental_score")])
        ws.append(["Economic Score", score.get("economic_score")])
        ws.append([])
        ws.append(["SOLAR & WIND POTENTIAL"])
        ws.append(["Solar Capacity Factor (%)", solar.get("capacity_factor_pct")])
        ws.append(["Solar Expected Output (MWh/yr)", solar.get("expected_energy_output_mwh_year")])
        ws.append(["Wind Capacity Factor (%)", wind.get("capacity_factor_pct")])
        ws.append(["Wind Expected Output (MWh/yr)", wind.get("expected_annual_energy_mwh")])
        ws.append([])
        ws.append(["FORECAST & FINANCIALS"])
        ws.append(["Year 1 Generation (MWh)", forecast.get("year1_mwh")])
        ws.append(["Year 5 Generation (MWh)", forecast.get("year5_mwh")])
        ws.append(["Year 10 Generation (MWh)", forecast.get("year10_mwh")])
        ws.append(["Year 25 Generation (MWh)", forecast.get("year25_mwh")])
        ws.append(["Estimated CAPEX ($)", forecast.get("estimated_capex_usd")])
        ws.append(["Est. Annual Revenue ($)", forecast.get("estimated_annual_revenue_usd")])
        ws.append(["Payback Period (Years)", forecast.get("payback_period_years")])

        out = io.BytesIO()
        wb.save(out)
        return out.getvalue()
    except Exception:
        # Fallback CSV format
        out = io.StringIO()
        writer = csv.writer(out)
        site = site_data.get('site', {})
        score = site_data.get('score', {})
        writer.writerow(["Site Name", site.get("name")])
        writer.writerow(["Latitude", site.get("latitude")])
        writer.writerow(["Longitude", site.get("longitude")])
        writer.writerow(["Overall Score", score.get("overall_score")])
        writer.writerow(["Category", score.get("category")])
        writer.writerow(["Recommendation", score.get("recommended_technology")])
        return out.getvalue().encode('utf-8')
