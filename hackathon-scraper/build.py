def main():
    import shutil, os

    static_src = 'src/static'                 # has index.html, css, js, etc.
    data_src   = 'data/hackathons.json'       # produced by your scraper step

    build_dir = 'build'
    data_dir  = os.path.join(build_dir, 'data')

    # fresh build
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)

    # copy static assets so index.html ends up at build/index.html
    shutil.copytree(static_src, build_dir, dirs_exist_ok=True)

    # copy data
    os.makedirs(data_dir, exist_ok=True)
    shutil.copy(data_src, os.path.join(data_dir, 'hackathons.json'))

    print("Build completed successfully.")

if __name__ == '__main__':
    main()
