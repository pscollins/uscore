import flask

app = flask.Flask(__name__)

@app.route('/about')
def about()
    return 'foo'

@app.route('/')
@app.route('/main/<key>')
def display_table(key='in comments count unique'):
    title = 'FOO'
    column_names = ['a', 'b', 'c']
    rows = [[1, 2, 3] for x in range(0, 10)]
    return flask.render_template('index.html',
                                 title=title,
                                 column_names=column_names,
                                 rows=rows)


if __name__ == '__main__':
    app.debug = True
    app.run()
