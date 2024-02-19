<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registration form</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <?php
        // print_r method tell us what the variable has currently
        // print_r($_POST);
        if (isset($_POST["submit"])){
            # code...
            $f_name = $_POST["first_name"];
            $l_name = $_POST["last_name"];
            $email = $_POST["email"];
            $contact = $_POST["contact"];
            $fam1 = $_POST["fam1"];
            $fam2 = $_POST["fam2"];
            $password = $_POST["password"];
            $conf_pass = $_POST["confirm_password"];
            
            $pass_hash = password_hash($password, PASSWORD_DEFAULT);
            // echo "Stored Hash: " . $pass_hash;            

            $errors = array();
            
            // validating the form details
            if (empty($f_name) OR empty($l_name) OR empty($contact) OR empty($email) OR empty($fam1) OR empty($fam2) OR empty($password) OR empty($conf_pass)) {
                array_push($errors, "All fields required");
            }
            else{

                if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
                    array_push($errors, "Invalid email");
                }
                if (strlen($contact)<10 OR strlen($contact)<10) {
                    array_push($errors, "Contact no. must be of 10 digits");
                }
                if (strlen($fam1)<10 OR strlen($fam1)>10) {
                    array_push($errors, "Contact no. must be of 10 digits");
                }
                if (strlen($fam2)<10 OR strlen($fam2)>10) {
                    array_push($errors, "Contact no. must be of 10 digits");
                }
                if (strlen($password)<8) {
                    array_push($errors, "Password must be 8 characters long");
                }
                if ($password!==$conf_pass) {
                    array_push($errors, "Password doesn't match");
                }
            }

            require_once "database.php";
            $sql = "SELECT * FROM users WHERE email = '$email'";
            $result = mysqli_query($conn, $sql);
            $row_count =mysqli_num_rows($result);
            if($row_count>0) {
                array_push($errors, "Email already registered");
            }

            if(count($errors)>0) {
                foreach ($errors as $error) {
                    echo "<div class='alert alert-danger'>$error</div>";
                }
            }else{
                // we will insert the data in the database
                require_once "database.php";

                $sql = "INSERT INTO users (first_name, last_name, email, contact, fam1, fam2, password) VALUES (?, ?, ?, ?, ?, ?, ?)";
                // Initialize a statement and return an object to use with stmt_prepare()
                $stmt = mysqli_stmt_init($conn);
                $prepareStmt = mysqli_stmt_prepare($stmt, $sql);
                if ($prepareStmt) {
                    mysqli_stmt_bind_param($stmt, "sssssss", $f_name, $l_name, $email, $contact, $fam1, $fam2, $pass_hash);
                    mysqli_stmt_execute($stmt);
                    echo "<div class = 'alert alert-success'>You are registered successfully.</div>";
                }else{
                    die("Something went wrong");
                }
            }
        }
        ?>
        <form action="registration.php" method="post">
            <div class="form-group">
                <input type="text" class="form-control" name="first_name" placeholder="First Name">
            </div>
            <div class="form-group">
                <input type="text" class="form-control" name="last_name" placeholder="Last Name">
            </div>
            <div class="form-group">
                <input type="text" class="form-control" name="email" placeholder="Email">
            </div>
            <div class="form-group">
                <input type="text" class="form-control" name="contact" placeholder="Contact">
            </div>
            <div class="form-group">
                <input type="text" class="form-control" name="fam1" placeholder="Member1">
            </div>
            <div class="form-group">
                <input type="text" class="form-control" name="fam2" placeholder="Member2">
            </div>
            <!-- <div class="form-group">
                <input type="text" class="form-control" name="fam3" placeholder="Member3">
            </div> -->
            <div class="form-group">
                <input type="password" class="form-control" name="password" placeholder="Password">
            </div>
            <div class="form-group">
                <input type="password" class="form-control" name="confirm_password" placeholder="Confirm Password">
            </div>
            <div class="form-btn">
                <input type="submit" class="btn btn-primary" value="Register" name="submit">
            </div>
        </form>
    </div>
</body>
</html>