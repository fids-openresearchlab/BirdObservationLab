<!-- PROJECT LOGO -->
<br />


<div align="center">
<!--
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>
-->
  <h3 align="center">BirdObservationLab</h3>

  <p align="center">
    A flying bird observation system
    <br />
    <a href="https://fids-openresearchlab.github.io/BirdObservationLab/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <!---
    <a href="https://github.com/othneildrew/Best-README-Template">View Demo</a>
    ·
    -->
    <a href="https://github.com/fidsopenresearchlab/BirdObservationLab/issues">Report Bug</a>
    ·
    <a href="https://github.com/fidsopenresearchlab/BirdObservationLab/issues">Request Feature</a>
  </p>
</div>




<!-- ABOUT THE PROJECT -->
## About The Project

BirdObservationLab allows to detect and track flying birds in zenith faced high resolution footage. 

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/fids-openresearchlab/BirdObservationLab.git
   ```
2. Install dependencies using poetry:
    ```shell
    poetry install
    ```

Important: Make sure your OpenCV Version can use CUDA functionality.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Please check out our [Documentation]("https://fids-openresearchlab.github.io/BirdObservationLab/) in order to properly configurating and using this project.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap
- [ ] Update Documentation
- [ ] Bird Classification
- [ ] Streamlit based webapp

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing
If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact and Links
Project Link: https://fids-openresearchlab.org/

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Use this space to list resources you find helpful and would like to give credit to. I've included a few of my favorites to kick things off!
* [Yupi](https://github.com/yupidevs/yupi)


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/othneildrew
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com

<!---
## Restart Stream automatically
crontab -e
@reboot  /home/fids/fids_bird_detection_and_tracking/run_stream_job.py
*/5 * * * * /home/fids/fids_bird_detection_and_tracking/run_stream_job.py


## Docker

### Create Networks

```docker network create -d bridge fids-network```

``` docker network create nats-network```

### Local mongoDB

#### Pull mongoDB docker image

```
docker pull mongo
```

#### Start a mongo server

The environment variables `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` should be set respectively.

```
docker run -p 27017:27017 --env MONGO_INITDB_ROOT_USERNAME=<username> --env MONGO_INITDB_ROOT_PASSWORD=<password> --name fids_mongo -t -i --network fids-network --network-alias mongo --rm mongo:latest

```

nohup python3 detection_worker.py -source /media/kubus/kubus_data/data/ressources/footage -weights_path
/media/kubus/kubus_data/data/detection/yolov4/yolov4-bird_last.weights -yolo_config_path
/media/kubus/kubus_data/data/detection/yolov4/yolov4-bird.cfg & exit

-->