<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Form</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">

        <?php
        if (isset($_POST["login"])) {
            $email = $_POST["email"];
            $pass = $_POST["password"];
            require_once "database.php";
            $sql = "SELECT * FROM users WHERE email = '$email'";
            $result = mysqli_query($conn, $sql);
            $user = mysqli_fetch_array($result, MYSQLI_ASSOC);
            if ($user) {
                // echo "Stored Hash: " . $user["password"];
                // echo "Entered Hash: " . password_hash($pass, PASSWORD_DEFAULT);
                if (password_verify($pass, $user["password"])) {
                    $pythonScript = "python F:/xampp/htdocs/login-register/drowsiness_detection.py";
                     $output = shell_exec($pythonScript);
                    //  echo "Python Script Output: $output";

                     if ($output === null) {
                        echo "Error executing Python script.";
                    } else {
                        echo "Python Script Output: $output";
                    }
                    // header("Location: index.php");
                    // die();
                }
                else{
                    echo "<div class='alert alert-danger'>Invalid Password</div>";
                }
            }else{
                echo "<div class='alert alert-danger'>User doesn't exist</div>";
            }
        }
        ?>

        <form action="login.php" method="post">
            <div class="form-group">
                <input type="email" name="email" placeholder="Enter email" class="form-control">
            </div>
            <div class="form-group">
                <input type="password" name="password" placeholder="Enter Password" class="form-control">
            </div>
            <div class="form-btn">
                <input type="submit" value="Login" name="login" class="btn btn-primary">
            </div>
        </form>
    </div>
</body>
</html>