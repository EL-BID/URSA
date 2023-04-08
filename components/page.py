from dash import html


def pageContent(pageTitle, alerts, content):
    title = html.H2(
        pageTitle,
        style={'margin': '50px 0'}
    )
    ruler = html.Hr(style={'margin': '50px 0'})

    result = [title]
    result.extend(alerts)
    result.append(ruler)
    result.extend(content)

    return html.Div(result)
